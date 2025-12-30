from datetime import date

import pytest

from bulk_uploader.iterators import days_intervals

intervals_testdata = [
    (
        date(year=2025, month=9, day=1),
        date(year=2025, month=9, day=30),
        10,
        [
            (date(year=2025, month=9, day=1), date(year=2025, month=9, day=10)),
            (date(year=2025, month=9, day=11), date(year=2025, month=9, day=20)),
            (date(year=2025, month=9, day=21), date(year=2025, month=9, day=30)),
        ],
    ),
    (
        date(year=2025, month=9, day=1),
        date(year=2025, month=9, day=5),
        2,
        [
            (date(year=2025, month=9, day=1), date(year=2025, month=9, day=2)),
            (date(year=2025, month=9, day=3), date(year=2025, month=9, day=4)),
            (date(year=2025, month=9, day=5), date(year=2025, month=9, day=5)),
        ],
    ),
    (
        date(year=2025, month=9, day=1),
        date(year=2025, month=9, day=3),
        1,
        [
            (date(year=2025, month=9, day=1), date(year=2025, month=9, day=1)),
            (date(year=2025, month=9, day=2), date(year=2025, month=9, day=2)),
            (date(year=2025, month=9, day=3), date(year=2025, month=9, day=3)),
        ],
    ),
]


@pytest.mark.parametrize(
    "start_day,end_day,delta,expected_intervals", intervals_testdata
)
def test_days_intervals(start_day, end_day, delta, expected_intervals):
    intervals = [item for item in days_intervals(start_day, end_day, delta)]
    assert intervals == expected_intervals
