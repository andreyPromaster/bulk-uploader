import pytest
from datetime import timedelta
from unittest.mock import AsyncMock, patch

from bulk_uploader.manager import Ratelimit, UploadedData
from bulk_uploader.store import ListStore
from bulk_uploader.apicall import GetAPICall
from bulk_uploader.async_queue import AsyncQueue


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
    # Set unlimited queue size to prevent blocking during test
    uploaded_data._q = AsyncQueue(maxsize=0)

    # Mock the queue to capture puts
    put_calls = []
    original_put = uploaded_data._q.put
    async def mock_put(item):
        put_calls.append(item)
        await original_put(item)

    uploaded_data._q.put = mock_put

    await uploaded_data.url_gen()

    assert len(put_calls) == 10
    assert put_calls == urls


@pytest.mark.asyncio
async def test_rate_limit_batches_and_sleeps():
    """Test that with rate limit, items are batched and sleep is called."""
    store = ListStore()
    urls = [f"https://test.com/{i}" for i in range(7)]  # 7 items
    rate_limit = Ratelimit(num_requests=3, period=timedelta(seconds=1))
    uploaded_data = UploadedData(
        store=store,
        api_call_factory=GetAPICall,
        url_maker=urls,
        rate_limit=rate_limit,
    )
    # Replace queue with unlimited size to prevent QueueFull errors
    uploaded_data._q = AsyncQueue(maxsize=0)

    # Mock the internal queue's put_nowait to capture batch_put calls
    batch_put_calls = []
    original_put_nowait = uploaded_data._q._queue.put_nowait
    
    def mock_put_nowait(item):
        # Group items by batch for easier verification
        if not batch_put_calls or len(batch_put_calls[-1]) >= 3:
            batch_put_calls.append([])
        batch_put_calls[-1].append(item)
        original_put_nowait(item)

    uploaded_data._q._queue.put_nowait = mock_put_nowait

    with patch('bulk_uploader.manager.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        await uploaded_data.url_gen()

        # Should have 3 batches: [0,1,2], [3,4,5], [6]
        assert len(batch_put_calls) == 3
        assert batch_put_calls[0] == urls[:3]
        assert batch_put_calls[1] == urls[3:6]
        assert batch_put_calls[2] == urls[6:]

        # Sleep should be called twice (between batches)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(1.0)


@pytest.mark.asyncio
async def test_rate_limit_exact_batches():
    """Test rate limit with exact multiple of batch size."""
    store = ListStore()
    urls = [f"https://test.com/{i}" for i in range(6)]  # 6 items, batch of 3
    rate_limit = Ratelimit(num_requests=3, period=timedelta(seconds=2))
    uploaded_data = UploadedData(
        store=store,
        api_call_factory=GetAPICall,
        url_maker=urls,
        rate_limit=rate_limit,
    )
    # Replace queue with unlimited size to prevent QueueFull errors
    uploaded_data._q = AsyncQueue(maxsize=0)

    # Mock the internal queue's put_nowait to capture batch_put calls
    batch_put_calls = []
    original_put_nowait = uploaded_data._q._queue.put_nowait
    
    def mock_put_nowait(item):
        # Group items by batch for easier verification
        if not batch_put_calls or len(batch_put_calls[-1]) >= 3:
            batch_put_calls.append([])
        batch_put_calls[-1].append(item)
        original_put_nowait(item)

    uploaded_data._q._queue.put_nowait = mock_put_nowait

    with patch('bulk_uploader.manager.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        await uploaded_data.url_gen()

        # Two batches of 3
        assert len(batch_put_calls) == 2
        assert batch_put_calls[0] == urls[:3]
        assert batch_put_calls[1] == urls[3:]

        # Sleep is called after each full batch, so 2 times for 2 full batches
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(2.0)


@pytest.mark.asyncio
async def test_rate_limit_single_item():
    """Test rate limit with single item."""
    store = ListStore()
    urls = ["https://test.com/1"]
    rate_limit = Ratelimit(num_requests=5, period=timedelta(seconds=1))
    uploaded_data = UploadedData(
        store=store,
        api_call_factory=GetAPICall,
        url_maker=urls,
        rate_limit=rate_limit,
    )
    # Replace queue with unlimited size to prevent QueueFull errors
    uploaded_data._q = AsyncQueue(maxsize=0)

    # Mock the internal queue's put_nowait to capture batch_put calls
    batch_put_calls = []
    original_put_nowait = uploaded_data._q._queue.put_nowait
    
    def mock_put_nowait(item):
        # Group items by batch for easier verification
        if not batch_put_calls or len(batch_put_calls[-1]) >= 5:
            batch_put_calls.append([])
        batch_put_calls[-1].append(item)
        original_put_nowait(item)

    uploaded_data._q._queue.put_nowait = mock_put_nowait

    with patch('bulk_uploader.manager.asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        await uploaded_data.url_gen()

        # One batch with the single item
        assert len(batch_put_calls) == 1
        assert batch_put_calls[0] == urls

        # No sleep since only one batch
        assert mock_sleep.call_count == 0