from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from httpx import AsyncClient

from app.domain.calendar import week_start
from app.infrastructure.settings import settings


@pytest.mark.asyncio
async def test_object_access(client: AsyncClient) -> None:
    headers = {"X-Demo-User": "2"}

    get_tasks_response = await client.get("/api/tasks", headers=headers)

    assert get_tasks_response.json() == []

    response = await client.patch("/api/tasks/1", headers=headers, json={"status": "done"})

    assert response.status_code == 404

    get_tasks_response_2 = await client.get("/api/tasks/1", headers=headers)

    assert get_tasks_response_2.status_code == 404


@pytest.mark.asyncio
async def test_task_creation_and_persistence(client: AsyncClient) -> None:
    payload = {
        "title": "Подготовить встречу",
        "assignee_id": 3,
        "department_id": 1,
        "due_date": "2026-11-08",
    }

    response = await client.post("/api/tasks", json=payload)

    assert response.status_code == 201

    task_id = response.json()["id"]

    changed = await client.patch(f"/api/tasks/{task_id}", json={"status": "done"})

    assert changed.json()["status"] == "done"

    get_tasks_response = await client.get("/api/tasks")

    assert any(t["id"] == task_id and t["status"] == "done" for t in get_tasks_response.json())


@pytest.mark.asyncio
async def test_invalid_task_and_volunteer_create(client: AsyncClient) -> None:
    payload = {"title": "   ", "assignee_id": 3, "department_id": 1, "due_date": "2026-11-08"}

    post_tasks_response = await client.post("/api/tasks", json=payload)

    assert post_tasks_response.status_code == 422

    payload["title"] = "Задача"

    post_tasks_response_2 = await client.post(
        "/api/tasks", headers={"X-Demo-User": "2"}, json=payload
    )

    assert post_tasks_response_2.status_code == 403

    payload["assignee_id"] = 999

    post_tasks_response_3 = await client.post("/api/tasks", json=payload)

    assert post_tasks_response_3.status_code == 422


@pytest.mark.asyncio
async def test_week_isolation_and_review(client: AsyncClient) -> None:
    patch_week_items_response = await client.patch(
        "/api/week/items/1", headers={"X-Demo-User": "3"}, json={"done": True}
    )

    assert patch_week_items_response.status_code == 404

    get_week_response = await client.get("/api/week", headers={"X-Demo-User": "2"})

    assert get_week_response.status_code == 403

    created = await client.post("/api/week/items", json={"title": "План недели"})

    assert created.status_code == 201

    patch_week_items_response_2 = await client.patch(
        f"/api/week/items/{created.json()['id']}", json={"done": True}
    )

    assert patch_week_items_response_2.json()["done"]

    put_week_review_response = await client.put(
        "/api/week/review", json={"text": "Встреча проведена"}
    )

    assert put_week_review_response.status_code == 200

    get_week_response_2 = await client.get("/api/week")

    assert get_week_response_2.json()["review"] == "Встреча проведена"


@pytest.mark.asyncio
async def test_demo_disabled_fails_closed(client: AsyncClient) -> None:
    settings.demo_mode = False

    get_tasks_response = await client.get("/api/tasks")

    assert get_tasks_response.status_code == 401


@pytest.mark.asyncio
async def test_coexecutor_can_work_but_cannot_change_assignment(client: AsyncClient) -> None:
    response = await client.patch("/api/tasks/1", json={"coexecutor_ids": [2]})

    assert response.status_code == 200

    headers = {"X-Demo-User": "2"}

    get_tasks_response = await client.get("/api/tasks", headers=headers)

    assert len(get_tasks_response.json()) == 1

    detail = (await client.get("/api/tasks/1", headers=headers)).json()

    assert detail["can_contribute"] and not detail["can_edit"]

    patch_tasks_response = await client.patch(
        "/api/tasks/1", headers=headers, json={"title": "Изменить поручение"}
    )

    assert patch_tasks_response.status_code == 403

    result = await client.patch(
        "/api/tasks/1", headers=headers, json={"status": "done", "result": "Материалы готовы"}
    )

    assert result.status_code == 200
    assert result.json()["result"] == "Материалы готовы"

    post_tasks_comments_response = await client.post(
        "/api/tasks/1/comments", headers=headers, json={"text": "Согласовано с командой"}
    )

    assert post_tasks_comments_response.status_code == 201

    await client.patch("/api/tasks/1", json={"coexecutor_ids": []})
    get_tasks_response_2 = await client.get("/api/tasks/1", headers=headers)

    assert get_tasks_response_2.status_code == 404


@pytest.mark.asyncio
async def test_observer_and_department_colleague_are_read_only(client: AsyncClient) -> None:
    await client.patch("/api/tasks/1", json={"assignee_id": 1, "observer_ids": [2]})
    for user_id in (2, 3):
        headers = {"X-Demo-User": str(user_id)}

        detail = await client.get("/api/tasks/1", headers=headers)

        assert detail.status_code == 200
        assert not detail.json()["can_contribute"]

        patch_tasks_response = await client.patch(
            "/api/tasks/1", headers=headers, json={"status": "done"}
        )

        assert patch_tasks_response.status_code == 403

        post_tasks_comments_response = await client.post(
            "/api/tasks/1/comments", headers=headers, json={"text": "Текст"}
        )

        assert post_tasks_comments_response.status_code == 403

        post_tasks_checklist_response = await client.post(
            "/api/tasks/1/checklist", headers=headers, json={"title": "Пункт"}
        )

        assert post_tasks_checklist_response.status_code == 403


@pytest.mark.asyncio
async def test_stale_update_does_not_overwrite_new_data(client: AsyncClient) -> None:
    original = (await client.get("/api/tasks/1")).json()["task"]

    changed = await client.patch(
        "/api/tasks/1", json={"title": "Новое поручение", "expected_version": original["version"]}
    )

    assert changed.status_code == 200
    assert changed.json()["version"] == original["version"] + 1

    stale = await client.patch(
        "/api/tasks/1",
        json={"description": "Устаревшая правка", "expected_version": original["version"]},
    )

    assert stale.status_code == 409

    task = (await client.get("/api/tasks/1")).json()["task"]

    assert task["title"] == "Новое поручение" and task["description"] == ""


@pytest.mark.asyncio
async def test_comments_and_checklist_are_saved_and_bound_to_task(client: AsyncClient) -> None:
    headers = {"X-Demo-User": "3"}

    added = await client.post("/api/tasks/1/comments", headers=headers, json={"text": "  Готово  "})

    assert added.status_code == 201
    assert added.json()["author_id"] == 3 and added.json()["text"] == "Готово"
    assert added.json()["created_at"].endswith("Z")

    item = (
        await client.post(
            "/api/tasks/1/checklist", headers=headers, json={"title": "Проверить макет"}
        )
    ).json()
    patch_tasks_checklist_response = await client.patch(
        f"/api/tasks/1/checklist/{item['id']}", headers=headers, json={"done": True}
    )

    assert patch_tasks_checklist_response.status_code == 200

    second = (
        await client.post(
            "/api/tasks",
            json={
                "title": "Другая задача",
                "assignee_id": 3,
                "department_id": 1,
                "due_date": "2026-11-08",
            },
        )
    ).json()
    patch_tasks_checklist_response_2 = await client.patch(
        f"/api/tasks/{second['id']}/checklist/{item['id']}", json={"done": False}
    )

    assert patch_tasks_checklist_response_2.status_code == 404

    detail = (await client.get("/api/tasks/1")).json()

    assert detail["comments"][0]["text"] == "Готово"
    assert detail["checklist"][0]["done"] is True

    post_tasks_comments_response = await client.post("/api/tasks/1/comments", json={"text": "   "})

    assert post_tasks_comments_response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "changes",
    [
        {"title": None},
        {"title": "   "},
        {},
        {"expected_version": 1},
        {"observer_ids": [999]},
        {"coexecutor_ids": [2, 2]},
        {"coexecutor_ids": [3]},
        {"coexecutor_ids": [2], "observer_ids": [2]},
    ],
)
async def test_invalid_task_changes_leave_original_intact(
    client: AsyncClient, changes: dict[str, object]
) -> None:
    patch_tasks_response = await client.patch("/api/tasks/1", json=changes)

    assert patch_tasks_response.status_code == 422

    get_tasks_response = await client.get("/api/tasks/1")

    assert get_tasks_response.json()["task"]["version"] == 1


@pytest.mark.asyncio
async def test_closed_week_is_immutable_until_reopened(client: AsyncClient) -> None:
    post_week_close_response = await client.post("/api/week/close")

    assert post_week_close_response.status_code == 409

    await client.put("/api/week/review", json={"text": "Часть плана сделана, остальное перенесём"})
    closed = await client.post("/api/week/close")

    assert closed.status_code == 200 and closed.json()["closed_at"]
    assert closed.json()["items"][0]["done"] is False  # incomplete items do not block review

    for method, path, payload in [
        ("POST", "/api/week/items", {"title": "Поздняя задача"}),
        ("PATCH", "/api/week/items/1", {"done": True}),
        ("PUT", "/api/week/review", {"text": "Переписать итоги"}),
    ]:
        request_method_response = await client.request(method, path, json=payload)

        assert request_method_response.status_code == 409

    post_week_open_response = await client.post("/api/week/open")

    assert post_week_open_response.status_code == 409

    reopened = await client.post("/api/week/reopen")

    assert reopened.status_code == 200 and reopened.json()["closed_at"] is None

    patch_week_items_response = await client.patch("/api/week/items/1", json={"done": True})

    assert patch_week_items_response.status_code == 200

    get_week_response = await client.get("/api/week")

    assert get_week_response.json()["review"].startswith("Часть плана")


@pytest.mark.asyncio
async def test_planning_overview_is_admin_only_and_tracks_week_state(client: AsyncClient) -> None:
    get_planning_weeks_response = await client.get(
        "/api/planning/weeks", headers={"X-Demo-User": "3"}
    )

    assert get_planning_weeks_response.status_code == 403

    before = (await client.get("/api/planning/weeks")).json()

    assert {entry["user_id"] for entry in before} == {1, 3}
    assert next(e for e in before if e["user_id"] == 3)["plan"]["opened"] is False

    await client.post("/api/week/open", headers={"X-Demo-User": "3"})
    after = (await client.get("/api/planning/weeks")).json()

    assert next(e for e in after if e["user_id"] == 3)["plan"]["opened"] is True

    get_planning_weeks_response_2 = await client.get("/api/planning/weeks?week=2099-01-07")

    assert get_planning_weeks_response_2.status_code == 422

    get_week_response = await client.get("/api/week?week=2026-11-05")

    assert get_week_response.status_code == 422


@pytest.mark.asyncio
async def test_past_week_is_read_without_creating_new_plan(client: AsyncClient) -> None:
    current = week_start(datetime.now(ZoneInfo("Europe/Saratov")).date())
    previous = current - timedelta(days=7)

    old = await client.get(f"/api/week?week={previous.isoformat()}")

    assert old.status_code == 200
    assert old.json()["week"] == previous.isoformat()
    assert old.json()["opened"] is False and old.json()["items"] == []

    get_week_response = await client.get("/api/week")

    assert get_week_response.json()["items"][0]["title"] == "Чужой план"

    get_f_week_response = await client.get(
        f"/api/week?week={(current + timedelta(days=7)).isoformat()}"
    )

    assert get_f_week_response.status_code == 422


@pytest.mark.asyncio
async def test_review_without_plan_cannot_close_week(client: AsyncClient) -> None:
    headers = {"X-Demo-User": "3"}
    await client.put("/api/week/review", headers=headers, json={"text": "Итоги"})

    post_week_close_response = await client.post("/api/week/close", headers=headers)

    assert post_week_close_response.status_code == 409

    get_week_response = await client.get("/api/week", headers=headers)

    assert get_week_response.json()["closed_at"] is None
