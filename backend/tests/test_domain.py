from datetime import UTC, date, datetime

import pytest

from app.application.jobs import next_occurrence
from app.application.weeks import plan_is_late
from app.domain.access import can_access_task
from app.domain.calendar import is_reminder_day, week_start
from app.domain.models import Actor, Role


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 11, 4), date(2026, 11, 4)),
        (date(2026, 11, 10), date(2026, 11, 4)),
        (date(2026, 11, 11), date(2026, 11, 11)),
        (date(2026, 1, 1), date(2025, 12, 31)),
    ],
)
def test_week_boundaries(day: date, expected: date) -> None:
    result = week_start(day)

    assert result == expected


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 11, 7), False),
        (date(2026, 11, 9), False),
        (date(2026, 11, 8), True),
        (date(2026, 11, 10), True),
    ],
)
def test_reminder_weekends(day: date, expected: bool) -> None:
    result = is_reminder_day(day)

    assert result == expected


def test_memberships_and_roles_are_combined() -> None:
    actor = Actor(5, frozenset({Role.OFFICE, Role.VOLUNTEER}), frozenset({4, 5}))

    access_by_department = [can_access_task(actor, 1, 2, department) for department in (4, 5, 6)]

    assert access_by_department == [True, True, False]


def test_volunteer_cannot_read_unrelated_tasks() -> None:
    actor = Actor(5, frozenset({Role.VOLUNTEER}), frozenset({4}))

    unrelated = can_access_task(actor, 1, 2, 4)
    assigned = can_access_task(actor, 1, 5, 4)

    assert unrelated is False
    assert assigned is True


def test_admin_has_office_overview() -> None:
    actor = Actor(1, frozenset({Role.ADMIN}), frozenset())

    has_access = can_access_task(actor, 2, 3, 7)

    assert has_access is True


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 1, 31), date(2026, 2, 28)),
        (date(2028, 1, 31), date(2028, 2, 29)),
        (date(2026, 2, 28), date(2026, 3, 31)),
        (date(2026, 12, 31), date(2027, 1, 31)),
    ],
)
def test_monthly_recurrence_keeps_anchor(day: date, expected: date) -> None:
    result = next_occurrence(day, "monthly", 31)

    assert result == expected


def test_planning_deadline_uses_saratov_midnight() -> None:
    week = date(2026, 11, 4)
    before = datetime(2026, 11, 4, 19, 59, tzinfo=UTC)
    after = datetime(2026, 11, 4, 20, 0, tzinfo=UTC)

    unplanned_before_deadline = plan_is_late(week, None, False, before)
    unplanned_after_deadline = plan_is_late(week, None, False, after)
    planned_on_time = plan_is_late(week, before, True, after)
    planned_late = plan_is_late(week, after, True, after)
    legacy_plan = plan_is_late(week, None, True, after)

    assert unplanned_before_deadline is False
    assert unplanned_after_deadline is True
    assert planned_on_time is False
    assert planned_late is True
    assert legacy_plan is None
