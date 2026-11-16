from datetime import date, timedelta


def week_start(day: date) -> date:
    return day - timedelta(days=(day.weekday() - 2) % 7)


def is_reminder_day(day: date) -> bool:
    return day.weekday() not in {0, 5}
