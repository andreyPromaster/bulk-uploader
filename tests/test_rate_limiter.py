from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest

from bulk_uploader.apicall import GetAPICall
from bulk_uploader.async_queue import AsyncQueue
from bulk_uploader.manager import Ratelimit, UploadedData
from bulk_uploader.store import ListStore


@pytest.mark.asyncio
async def test_no_rate_limit():
    """Test that without rate limit, all URLs are put immediately."""
    store = ListStore()
    urls = [f"https://test.com/{i}" for i in range(10)]
    uploaded_data = UploadedData(
        store=store,
        api_call_factory=GetAPICall,
        url_maker=urls,
    )
    uploaded_data._q = AsyncQueue(maxsize=0)

    put_calls = []
    original_put = uploaded_data._q.put

    async def mock_put(item):
        put_calls.append(item)
        await original_put(item)

    uploaded_data._q.put = mock_put

    await uploaded_data.url_gen()

    assert len(put_calls) == 10
    assert put_calls == urls


@pytest.mark.parametrize(
    "urls_count, num_requests, period_seconds, sleep_count, sleep_value",
    [
        (7, 3, 1, 2, 1.0),
        (6, 3, 2, 2, 2.0),
        (1, 5, 1, 0, 1.0),
    ],
    ids=["batches_and_sleeps", "exact_batches", "single_item"],
)
@pytest.mark.asyncio
async def test_rate_limit(
    urls_count, num_requests, period_seconds, sleep_count, sleep_value
):
    """Test rate limiting with various configurations."""
    store = ListStore()
    urls = [f"https://test.com/{i}" for i in range(urls_count)]
    rate_limit = Ratelimit(
        num_requests=num_requests, period=timedelta(seconds=period_seconds)
    )
    uploaded_data = UploadedData(
        store=store,
        api_call_factory=GetAPICall,
        url_maker=urls,
        rate_limit=rate_limit,
    )
    uploaded_data._q = AsyncQueue(maxsize=0)

    batch_put_calls = []
    original_put_nowait = uploaded_data._q._queue.put_nowait

    def mock_put_nowait(item):
        if not batch_put_calls or len(batch_put_calls[-1]) >= num_requests:
            batch_put_calls.append([])
        batch_put_calls[-1].append(item)
        original_put_nowait(item)

    uploaded_data._q._queue.put_nowait = mock_put_nowait

    with patch(
        "bulk_uploader.manager.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        await uploaded_data.url_gen()

        expected_batches = [
            urls[i : i + num_requests] for i in range(0, len(urls), num_requests)
        ]
        assert len(batch_put_calls) == len(expected_batches)
        for actual_batch, expected_batch in zip(batch_put_calls, expected_batches):
            assert actual_batch == expected_batch

        assert mock_sleep.call_count == sleep_count
        if sleep_count > 0:
            mock_sleep.assert_called_with(sleep_value)
