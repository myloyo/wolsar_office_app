import calendar
from datetime import date, timedelta


def next_occurrence(day: date, frequency: str, anchor_day: int) -> date:
    if frequency == "weekly":
        return day + timedelta(days=7)
    month = day.month % 12 + 1
    year = day.year + (day.month == 12)
    return date(year, month, min(anchor_day, calendar.monthrange(year, month)[1]))
