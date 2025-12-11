from httpx import AsyncClient
import httpx
import pytest

from bulk_uploader.apicall import GetAPICall
from bulk_uploader.manager import UploadedData
from bulk_uploader.store import ListStore
from tests.fake_clients import RetryTransport


@pytest.mark.asyncio
async def test_save_data_ok():
    expected_data = {"fake_data": "value"}
    store = ListStore()
    fake_responses = [
        httpx.Response(200, json=expected_data),
        httpx.Response(200, json=expected_data),
    ]
    urls = ["https://test.com/1", "https://test.com/2"]
    uploaded_data = UploadedData(
        store=store,
        api_call_factory=GetAPICall,
        url_maker=urls,
        base_url="https://test.com",
    )
    await uploaded_data.run(
        transport=RetryTransport(handler=lambda item: "", responses=fake_responses)
    )

    assert uploaded_data.store.saved_data() == [expected_data, expected_data]
