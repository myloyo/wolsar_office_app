import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.calendar import week_start
from app.infrastructure.jobs import run_jobs
from app.infrastructure.models.auth import AuthRateRow, ChallengeRow, InvitationRow, SessionRow
from app.infrastructure.models.notifications import NotificationRow
from app.infrastructure.models.planning import WeekItemRow
from app.infrastructure.models.tasks import OccurrenceRow, RecurrenceRow, TaskRow
from app.infrastructure.models.workspace import UserRow
from app.infrastructure.settings import Settings, settings
from app.main import app


async def login(
    client: AsyncClient, email: str = "admin@example.test", **extra: object
) -> dict[str, object]:
    requested = await client.post("/api/auth/request-code", json={"email": email, **extra})
    assert requested.status_code == 200, requested.text
    payload = requested.json()
    assert payload["local_code"]
    verified = await client.post(
        "/api/auth/verify-code",
        json={"challenge_id": payload["challenge_id"], "code": payload["local_code"]},
    )
    assert verified.status_code == 200, verified.text
    client.headers["X-CSRF-Token"] = verified.json()["csrf_token"]
    return payload


async def ministry(client: AsyncClient) -> int:
    result = await client.post("/api/ministries", json={"name": "Команда", "department_id": 1})
    assert result.status_code == 201, result.text
    ident = result.json()["id"]
    for user_id in [2, 3]:
        response = await client.put(
            f"/api/ministries/{ident}/members", json={"user_id": user_id, "leader": user_id == 3}
        )
        assert response.status_code == 200
    return ident


def event_payload(**extra: object) -> dict[str, object]:
    return {
        "title": "Встреча",
        "starts_at": "2026-12-01T10:00:00+04:00",
        "ends_at": "2026-12-01T11:00:00+04:00",
        **extra,
    }


@pytest.mark.asyncio
async def test_login_cookie_csrf_replay_and_logout(client: AsyncClient, db: AsyncSession) -> None:
    settings.demo_mode = False

    get_tasks_response = await client.get("/api/tasks", headers={"X-Demo-User": "1"})

    assert get_tasks_response.status_code == 401

    payload = await login(client)
    get_auth_session_response = await client.get("/api/auth/session")

    assert get_auth_session_response.json()["authenticated"] is True

    get_bootstrap_response = await client.get("/api/bootstrap")

    assert get_bootstrap_response.json()["demo"] is False

    cookies = client.cookies.get("wolsar_session")

    stored = list(await db.scalars(select(SessionRow)))

    assert len(stored) == 1 and stored[0].id != cookies

    post_auth_verify_code_response = await client.post(
        "/api/auth/verify-code",
        json={"challenge_id": payload["challenge_id"], "code": payload["local_code"]},
    )

    assert post_auth_verify_code_response.status_code == 403

    token = client.headers.pop("X-CSRF-Token")

    patch_tasks_response = await client.patch("/api/tasks/1", json={"status": "done"})

    assert patch_tasks_response.status_code == 403

    client.headers["X-CSRF-Token"] = token

    patch_tasks_response_2 = await client.patch(
        "/api/tasks/1", headers={"Origin": "https://foreign.example"}, json={"status": "done"}
    )

    assert patch_tasks_response_2.status_code == 403

    patch_tasks_response_3 = await client.patch("/api/tasks/1", json={"status": "done"})

    assert patch_tasks_response_3.status_code == 200

    post_auth_logout_response = await client.post("/api/auth/logout")

    assert post_auth_logout_response.status_code == 200

    get_tasks_response_2 = await client.get("/api/tasks")

    assert get_tasks_response_2.status_code == 401


@pytest.mark.asyncio
async def test_otp_limits_expiry_and_unknown_account(client: AsyncClient, db: AsyncSession) -> None:
    first = (
        await client.post("/api/auth/request-code", json={"email": "admin@example.test"})
    ).json()
    post_auth_request_code_response = await client.post(
        "/api/auth/request-code", json={"email": "admin@example.test"}
    )

    assert post_auth_request_code_response.status_code == 429

    wrong = "000000" if first["local_code"] != "000000" else "111111"
    for _ in range(5):
        post_auth_verify_code_response = await client.post(
            "/api/auth/verify-code", json={"challenge_id": first["challenge_id"], "code": wrong}
        )

        assert post_auth_verify_code_response.status_code == 403

    post_auth_verify_code_response_2 = await client.post(
        "/api/auth/verify-code",
        json={"challenge_id": first["challenge_id"], "code": first["local_code"]},
    )

    assert post_auth_verify_code_response_2.status_code == 403

    unknown = await client.post("/api/auth/request-code", json={"email": "unknown@example.test"})

    assert unknown.status_code == 200 and unknown.json()["local_code"] is None

    office = (
        await client.post("/api/auth/request-code", json={"email": "office@example.test"})
    ).json()
    await db.execute(
        update(ChallengeRow)
        .where(ChallengeRow.id == office["challenge_id"])
        .values(expires_at=datetime.now(UTC) - timedelta(seconds=1))
    )
    await db.commit()
    post_auth_verify_code_response_3 = await client.post(
        "/api/auth/verify-code",
        json={"challenge_id": office["challenge_id"], "code": office["local_code"]},
    )

    assert post_auth_verify_code_response_3.status_code == 403


@pytest.mark.asyncio
async def test_recovery_revokes_previous_sessions(client: AsyncClient, db: AsyncSession) -> None:
    settings.demo_mode = False
    await login(client)
    previous = client.cookies.get("wolsar_session")
    await db.execute(delete(AuthRateRow))
    await db.execute(
        update(ChallengeRow).values(created_at=datetime.now(UTC) - timedelta(minutes=2))
    )
    await db.commit()
    await login(client, purpose="recovery")

    get_auth_sessions_response = await client.get("/api/auth/sessions")

    assert len(get_auth_sessions_response.json()) == 1

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies={"wolsar_session": previous},
    ) as old:
        get_tasks_response = await old.get("/api/tasks")

        assert get_tasks_response.status_code == 401


@pytest.mark.asyncio
async def test_invitation_requires_code_and_preserves_user_roles(client: AsyncClient) -> None:
    invited = await client.post(
        "/api/admin/invitations",
        json={
            "name": "Новый сотрудник",
            "email": "new@example.test",
            "roles": ["office"],
            "department_ids": [1],
        },
    )

    assert invited.status_code == 201
    assert invited.json()["user"]["active"] is False

    request_without_invite = await client.post(
        "/api/auth/request-code", json={"email": "new@example.test"}
    )

    assert request_without_invite.json()["local_code"] is None

    get_admin_users_response = await client.get("/api/admin/users", headers={"X-Demo-User": "2"})

    assert get_admin_users_response.status_code == 403


@pytest.mark.asyncio
async def test_invitation_activation_and_expired_invitation(
    client: AsyncClient, db: AsyncSession
) -> None:
    result = (
        await client.post(
            "/api/admin/invitations",
            json={
                "name": "Новый",
                "email": "join@example.test",
                "roles": ["volunteer"],
                "department_ids": [],
            },
        )
    ).json()

    await login(client, "join@example.test", invitation=result["invitation"])
    bootstrap = (await client.get("/api/bootstrap")).json()

    assert bootstrap["current_user_id"] == result["user"]["id"]

    get_admin_users_response = await client.get("/api/admin/users")

    assert get_admin_users_response.status_code == 403

    post_auth_logout_response = await client.post("/api/auth/logout")

    assert post_auth_logout_response.status_code == 200

    expired = (
        await client.post(
            "/api/admin/invitations",
            json={
                "name": "Истёк",
                "email": "expired@example.test",
                "roles": ["volunteer"],
                "department_ids": [],
            },
        )
    ).json()
    await db.execute(
        update(InvitationRow)
        .where(InvitationRow.email == "expired@example.test")
        .values(expires_at=datetime.now(UTC) - timedelta(days=1))
    )
    await db.commit()
    response = await client.post(
        "/api/auth/request-code",
        json={"email": "expired@example.test", "invitation": expired["invitation"]},
    )

    assert response.json()["local_code"] is None


@pytest.mark.asyncio
async def test_admin_cannot_disable_self_and_disabled_sessions_fail(
    client: AsyncClient, db: AsyncSession
) -> None:
    put_admin_users_response = await client.put(
        "/api/admin/users/1",
        json={"name": "Админ", "roles": ["admin"], "department_ids": [1], "active": False},
    )

    assert put_admin_users_response.status_code == 409

    await login(client, "office@example.test")
    user = await db.get(UserRow, 3)

    assert user is not None

    user.active = False

    await db.commit()
    get_tasks_response = await client.get("/api/tasks")

    assert get_tasks_response.status_code == 401


def test_production_refuses_demo_and_insecure_configuration() -> None:
    with pytest.raises(ValidationError):
        Settings(app_env="production", demo_mode=True)
    with pytest.raises(ValidationError):
        Settings(app_env="production", demo_mode=False, otp_delivery="smtp", cookie_secure=False)


@pytest.mark.asyncio
async def test_scoped_membership_and_publications(client: AsyncClient) -> None:
    ident = await ministry(client)
    scope = f"/api/spaces/ministry/{ident}"

    get_scope_response = await client.get(scope, headers={"X-Demo-User": "2"})

    assert get_scope_response.status_code == 200

    post_scope_posts_response = await client.post(
        scope + "/posts", headers={"X-Demo-User": "2"}, json={"text": "Нельзя"}
    )

    assert post_scope_posts_response.status_code == 403

    post_scope_posts_response_2 = await client.post(
        scope + "/posts", headers={"X-Demo-User": "3"}, json={"text": "Встреча команды"}
    )

    assert post_scope_posts_response_2.status_code == 201

    get_scope_response_2 = await client.get(scope, headers={"X-Demo-User": "2"})

    assert get_scope_response_2.json()["posts"][0]["text"] == "Встреча команды"

    await client.delete(f"/api/ministries/{ident}/members/2")
    get_scope_response_3 = await client.get(scope, headers={"X-Demo-User": "2"})

    assert get_scope_response_3.status_code == 404


@pytest.mark.asyncio
async def test_room_conflicts_adjacent_booking_cancellation_and_versions(
    client: AsyncClient,
) -> None:
    room = (await client.post("/api/rooms", json={"name": "Зал"})).json()["id"]
    payload = event_payload(room_id=room)

    first = await client.post("/api/events", json=payload)

    assert first.status_code == 201, first.text

    post_events_response = await client.post("/api/events", json=payload)

    assert post_events_response.status_code == 409

    post_events_response_2 = await client.post(
        "/api/events",
        json=event_payload(
            room_id=room,
            starts_at="2026-12-01T11:00:00+04:00",
            ends_at="2026-12-01T12:00:00+04:00",
        ),
    )

    assert post_events_response_2.status_code == 201

    event_id = first.json()["id"]

    put_f_events_response = await client.put(
        f"/api/events/{event_id}", json={**payload, "cancelled": True, "expected_version": 1}
    )

    assert put_f_events_response.status_code == 200

    post_events_response_3 = await client.post("/api/events", json=payload)

    assert post_events_response_3.status_code == 201

    put_f_events_response_2 = await client.put(
        f"/api/events/{event_id}", json={**payload, "expected_version": 1}
    )

    assert put_f_events_response_2.status_code == 409


@pytest.mark.asyncio
async def test_calendar_privacy_and_leader_scope(client: AsyncClient) -> None:
    ident = await ministry(client)
    private = event_payload(scope="ministry", scope_id=ident)

    post_events_response = await client.post(
        "/api/events", headers={"X-Demo-User": "3"}, json=private
    )

    assert post_events_response.status_code == 201

    post_events_response_2 = await client.post(
        "/api/events", headers={"X-Demo-User": "2"}, json=private
    )

    assert post_events_response_2.status_code == 403

    await client.delete(f"/api/ministries/{ident}/members/2")
    events = (
        await client.get(
            "/api/events?start=2026-12-01&end=2026-12-31", headers={"X-Demo-User": "2"}
        )
    ).json()

    assert events == []

    post_events_response_3 = await client.post(
        "/api/events", json=event_payload(starts_at="2026-12-01T10:00:00")
    )

    assert post_events_response_3.status_code == 422


@pytest.mark.asyncio
async def test_slots_capacity_and_replacement(client: AsyncClient) -> None:
    ident = await ministry(client)
    event_id = (await client.post("/api/events", json=event_payload())).json()["id"]

    result = await client.post(
        "/api/slots",
        json={"event_id": event_id, "ministry_id": ident, "title": "Звук", "capacity": 1},
    )

    assert result.status_code == 201, result.text

    slot_id = result.json()["id"]

    post_slots_signup_response = await client.post(
        f"/api/slots/{slot_id}/signup", headers={"X-Demo-User": "2"}
    )

    assert post_slots_signup_response.status_code == 200

    post_slots_signup_response_2 = await client.post(
        f"/api/slots/{slot_id}/signup", headers={"X-Demo-User": "3"}
    )

    assert post_slots_signup_response_2.status_code == 409

    post_slots_replacement_response = await client.post(
        f"/api/slots/{slot_id}/replacement", headers={"X-Demo-User": "2"}
    )

    assert post_slots_replacement_response.status_code == 200

    post_slots_signup_response_3 = await client.post(
        f"/api/slots/{slot_id}/signup", headers={"X-Demo-User": "3"}
    )

    assert post_slots_signup_response_3.status_code == 200

    notes = (await client.get("/api/notifications", headers={"X-Demo-User": "3"})).json()

    assert any("замена" in note["title"] for note in notes)


@pytest.mark.asyncio
async def test_service_program_mc_timer_and_prayer_share_state(
    client: AsyncClient, db: AsyncSession
) -> None:
    result = await client.post("/api/services", json={"day": "2026-12-06", "kind": "1 ВС"})

    assert result.status_code == 201, result.text

    service = result.json()

    assert datetime.fromisoformat(service["event"]["starts_at"]).hour == 6

    event_id = service["event"]["id"]

    post_services_response = await client.post(
        "/api/services", json={"day": "2026-12-06", "kind": "1 ВС"}
    )

    assert post_services_response.status_code == 409

    program = service["program"]
    program["mc"]["text"] = "Добро пожаловать"
    program["assignments"]["Звук"] = 2

    saved = await client.put(
        f"/api/services/{event_id}/program", json={**program, "expected_version": 1}
    )

    assert saved.status_code == 200, saved.text

    get_f_services_response = await client.get(f"/api/services/{event_id}")

    assert get_f_services_response.json()["program"]["mc"]["text"] == "Добро пожаловать"

    put_services_program_response = await client.put(
        f"/api/services/{event_id}/program", json={**program, "expected_version": 1}
    )

    assert put_services_program_response.status_code == 409

    post_services_timer_response = await client.post(
        f"/api/services/{event_id}/timer",
        headers={"X-Demo-User": "2"},
        json={"action": "start", "expected_version": 2},
    )

    assert post_services_timer_response.status_code == 403

    running = await client.post(
        f"/api/services/{event_id}/timer", json={"action": "start", "expected_version": 2}
    )

    assert running.status_code == 200 and running.json()["timer"]["running"]

    put_services_program_response_2 = await client.put(
        f"/api/services/{event_id}/program", json={**program, "expected_version": 3}
    )

    assert put_services_program_response_2.status_code == 409

    await client.post(
        f"/api/services/{event_id}/timer", json={"action": "pause", "expected_version": 3}
    )
    prayer = (
        await client.post(
            "/api/prayers",
            headers={"X-Demo-User": "2"},
            json={"title": "Благословение", "details": "Приватные детали"},
        )
    ).json()
    linked = await client.post(f"/api/prayers/{prayer['id']}/schedule", json={"event_id": event_id})

    assert linked.status_code == 200
    assert any(b["id"] == f"prayer-{prayer['id']}" for b in linked.json()["program"]["blocks"])
    assert "Приватные детали" not in linked.text

    db.add(UserRow(id=4, name="Другой", roles=["volunteer"], department_ids=[], active=True))

    await db.commit()
    get_prayers_response = await client.get("/api/prayers", headers={"X-Demo-User": "4"})

    assert get_prayers_response.json() == []


@pytest.mark.asyncio
async def test_files_are_private_validated_and_recoverable(
    client: AsyncClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "storage_path", str(tmp_path / "uploads"))

    file = await client.post(
        "/api/files?scope=task&scope_id=1&name=notes.txt", content="Материалы".encode()
    )

    assert file.status_code == 201, file.text

    file_id = file.json()["id"]

    downloaded = await client.get(f"/api/files/{file_id}/download")

    assert downloaded.content.decode() == "Материалы"
    assert "attachment" in downloaded.headers["content-disposition"]

    get_files_download_response = await client.get(
        f"/api/files/{file_id}/download", headers={"X-Demo-User": "2"}
    )

    assert get_files_download_response.status_code == 404

    post_files_response = await client.post(
        "/api/files?scope=task&scope_id=1&name=../outside.txt", content=b"test"
    )

    assert post_files_response.status_code == 422

    post_files_response_2 = await client.post(
        "/api/files?scope=task&scope_id=1&name=bad.png", content=b"not an image"
    )

    assert post_files_response_2.status_code == 422

    delete_f_files_response = await client.delete(f"/api/files/{file_id}")

    assert delete_f_files_response.status_code == 200

    get_files_download_response_2 = await client.get(f"/api/files/{file_id}/download")

    assert get_files_download_response_2.status_code == 404

    await client.post(f"/api/files/{file_id}/restore")
    get_files_download_response_3 = await client.get(f"/api/files/{file_id}/download")

    assert get_files_download_response_3.status_code == 200


@pytest.mark.asyncio
async def test_comment_and_checklist_edit_delete_restore(client: AsyncClient) -> None:
    comment = (
        await client.post(
            "/api/tasks/1/comments", headers={"X-Demo-User": "3"}, json={"text": "Исходный"}
        )
    ).json()
    await client.patch("/api/tasks/1", json={"observer_ids": [2]})

    path = f"/api/tasks/1/comments/{comment['id']}"

    put_path_response = await client.put(
        path, headers={"X-Demo-User": "2"}, json={"text": "Чужая правка"}
    )

    assert put_path_response.status_code == 403

    put_path_response_2 = await client.put(
        path, headers={"X-Demo-User": "3"}, json={"text": "Исправлен"}
    )

    assert put_path_response_2.status_code == 200

    await client.delete(path)
    get_tasks_response = await client.get("/api/tasks/1")

    assert get_tasks_response.json()["comments"][0]["deleted"] is True

    await client.post(path + "/restore")
    get_tasks_response_2 = await client.get("/api/tasks/1")

    assert get_tasks_response_2.json()["comments"][0]["text"] == "Исправлен"

    item = (await client.post("/api/tasks/1/checklist", json={"title": "Старое"})).json()

    item_path = f"/api/tasks/1/checklist/{item['id']}"

    await client.put(item_path, json={"title": "Новое"})
    await client.delete(item_path)
    patch_item_path_response = await client.patch(item_path, json={"done": True})

    assert patch_item_path_response.status_code == 404

    await client.post(item_path + "/restore")
    get_tasks_response_3 = await client.get("/api/tasks/1")

    assert get_tasks_response_3.json()["checklist"][0]["title"] == "Новое"


@pytest.mark.asyncio
async def test_goals_priorities_week_links_report_and_carry(
    client: AsyncClient, db: AsyncSession
) -> None:
    current = week_start(
        datetime.now(UTC).astimezone(__import__("zoneinfo").ZoneInfo("Europe/Saratov")).date()
    )
    month = current.isoformat()[:7]
    goal = (
        await client.post("/api/planning/goals", json={"title": "Цель", "year": current.year})
    ).json()
    priority = await client.post(
        "/api/planning/priorities",
        headers={"X-Demo-User": "3"},
        json={"title": "Приоритет", "month": month, "department_id": 1, "goal_id": goal["id"]},
    )

    assert priority.status_code == 201, priority.text

    linked = await client.post(
        "/api/week/items",
        headers={"X-Demo-User": "3"},
        json={
            "title": "По задаче",
            "task_id": 1,
            "priority_id": priority.json()["id"],
            "section": "Проекты",
        },
    )

    assert linked.status_code == 201 and linked.json()["task_id"] == 1

    post_week_items_response = await client.post(
        "/api/week/items", json={"title": "Неверно", "task_id": 999}
    )

    assert post_week_items_response.status_code == 422

    report = await client.get(f"/api/planning/report?month={month}")

    assert report.status_code == 200 and report.json()["weeks"]

    get_planning_report_response = await client.get(
        f"/api/planning/report?month={month}", headers={"X-Demo-User": "3"}
    )

    assert get_planning_report_response.status_code == 403

    db.add(UserRow(id=4, name="Офис", roles=["office"], department_ids=[1], active=True))

    await db.flush()

    old = WeekItemRow(user_id=4, week=current - timedelta(days=7), title="Перенести", done=False)
    db.add(old)
    db.add(WeekItemRow(user_id=4, week=current - timedelta(days=7), title="Готовое", done=True))

    await db.commit()
    opened = await client.post("/api/week/open", headers={"X-Demo-User": "4"})

    assert opened.status_code == 200 and len(opened.json()["items"]) == 1

    again = await client.post("/api/week/open", headers={"X-Demo-User": "4"})

    assert len(again.json()["items"]) == 1
    assert again.json()["items"][0]["carried_from_id"] == old.id


@pytest.mark.asyncio
async def test_jobs_recurrences_and_reminders_are_idempotent(
    client: AsyncClient, db: AsyncSession
) -> None:
    db.add(
        RecurrenceRow(
            task_id=1,
            frequency="monthly",
            next_date=datetime(2026, 11, 4).date(),
            anchor_day=4,
            active=True,
            revision=1,
        )
    )
    await db.commit()
    now = datetime(2026, 11, 4, 8, tzinfo=UTC)

    await run_jobs(db, now)
    await run_jobs(db, now)
    scalars_ccurrence_ow_response = await db.scalars(select(OccurrenceRow))

    assert len(list(scalars_ccurrence_ow_response)) == 1

    notes = list(await db.scalars(select(NotificationRow)))

    assert len({n.dedupe_key for n in notes}) == len(notes)

    scalars_ask_ow_response = await db.scalars(select(TaskRow))

    assert len(list(scalars_ask_ow_response)) == 2


@pytest.mark.asyncio
async def test_room_booking_is_atomic_for_concurrent_requests(client: AsyncClient) -> None:
    room = (await client.post("/api/rooms", json={"name": "Один зал"})).json()["id"]

    results = await asyncio.gather(
        *[client.post("/api/events", json=event_payload(room_id=room)) for _ in range(2)]
    )

    assert sorted(r.status_code for r in results) == [201, 409]


@pytest.mark.asyncio
async def test_last_slot_cannot_be_taken_twice(client: AsyncClient) -> None:
    ident = await ministry(client)
    event_id = (await client.post("/api/events", json=event_payload())).json()["id"]
    slot_id = (
        await client.post(
            "/api/slots",
            json={
                "event_id": event_id,
                "ministry_id": ident,
                "title": "Последнее место",
                "capacity": 1,
            },
        )
    ).json()["id"]

    results = await asyncio.gather(
        *[
            client.post(f"/api/slots/{slot_id}/signup", headers={"X-Demo-User": str(user_id)})
            for user_id in [2, 3]
        ]
    )

    assert sorted(r.status_code for r in results) == [200, 409]


@pytest.mark.asyncio
async def test_admin_email_recovery_preserves_identity_and_requires_new_code(
    client: AsyncClient, db: AsyncSession
) -> None:
    result = await client.post(
        "/api/admin/users/3/recovery", json={"email": "restored@example.test"}
    )

    assert result.status_code == 200, result.text

    user = await db.get(UserRow, 3)

    assert user is not None and user.email == "restored@example.test" and not user.active

    get_ask_ow_response = await db.get(TaskRow, 1)

    assert get_ask_ow_response.assignee_id == 3

    await login(client, "restored@example.test", invitation=result.json()["invitation"])
    get_bootstrap_response = await client.get("/api/bootstrap")

    assert get_bootstrap_response.json()["current_user_id"] == 3


@pytest.mark.asyncio
async def test_notification_ownership_and_push_endpoint_validation(client: AsyncClient) -> None:
    await client.post("/api/tasks/1/comments", json={"text": "Новое сообщение"})

    notes = (await client.get("/api/notifications", headers={"X-Demo-User": "3"})).json()

    assert notes

    post_notifications_read_response = await client.post(
        f"/api/notifications/{notes[0]['id']}/read", headers={"X-Demo-User": "2"}
    )

    assert post_notifications_read_response.status_code == 404

    post_push_subscribe_response = await client.post(
        "/api/notifications/push/subscribe",
        json={
            "endpoint": "https://127.0.0.1/private",
            "keys": {"auth": "a" * 20, "p256dh": "a" * 80},
        },
    )

    assert post_push_subscribe_response.status_code == 422


@pytest.mark.asyncio
async def test_preparation_steps_are_stored_and_scoped(client: AsyncClient) -> None:
    ident = await ministry(client)

    result = await client.post(
        "/api/preparations",
        headers={"X-Demo-User": "3"},
        json={"ministry_id": ident, "title": "Встреча молодёжи", "kind": "МСЛ"},
    )

    assert result.status_code == 201

    prep = result.json()

    put_f_preparations_response = await client.put(
        f"/api/preparations/{prep['id']}",
        headers={"X-Demo-User": "3"},
        json={"completed": [0, 1]},
    )

    assert put_f_preparations_response.status_code == 200

    put_f_preparations_response_2 = await client.put(
        f"/api/preparations/{prep['id']}", headers={"X-Demo-User": "2"}, json={"completed": [2]}
    )

    assert put_f_preparations_response_2.status_code == 403

    get_preparations_response = await client.get("/api/preparations", headers={"X-Demo-User": "2"})

    assert get_preparations_response.json()[0]["completed"] == [0, 1]


async def test_calendar_normalizes_offsets_and_midnight(client: AsyncClient) -> None:
    result = await client.post(
        "/api/events",
        json=event_payload(
            starts_at="2026-12-01T00:30:00+04:00", ends_at="2026-12-01T01:30:00+04:00"
        ),
    )

    assert result.status_code == 201

    event = result.json()
    stamp = datetime.fromisoformat(event["starts_at"])

    assert stamp.hour == 20 and stamp.day == 30

    rows = (await client.get("/api/events?start=2026-12-01&end=2026-12-01")).json()

    assert any(row["id"] == event["id"] for row in rows)

    previous = (await client.get("/api/events?start=2026-11-30&end=2026-11-30")).json()

    assert all(row["id"] != event["id"] for row in previous)
