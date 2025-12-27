from datetime import date, timedelta
from typing import Generator


def loading_urls(base_url, provider):
    for item in provider:
        yield f"{base_url}/{item}"


def days_intervals(
    start: date, end: date, delta_days=1
) -> Generator[tuple[date, date], None, None]:
    """Split updating period into chunks"""
    delta = timedelta(days=delta_days)
    day_delta = timedelta(days=1)
    start_period = start
    while start_period <= end:
        end_period = start_period + delta - day_delta
        if end_period <= end:
            yield (start_period, end_period)
            start_period = end_period + day_delta
        else:
            yield (start_period, end)
            break


def id_iterator(start=0, end=50, step=1):
    for i in range(start, end, step):
        yield i
