from datetime import date, timedelta


def loading_urls(base_url, provider):
    for item in provider:
        yield f"{base_url}/{item}"


def get_days_interval(start: date, end: date, delta_days=1) -> list[list[date]]:
    """Split updating period into chunks"""
    delta = timedelta(days=delta_days)
    next_day_delta = timedelta(days=1)
    start_period = start
    while start_period <= end:
        end_period = start_period + delta
        if end_period <= end:
            yield (start_period, end_period)
            start_period = end_period + next_day_delta
        else:
            yield (start_period, end)
            break

def get_next_comment(start=1, max=50):
    for i in range(start, max+1):
        yield i
