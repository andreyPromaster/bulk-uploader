import httpx
import pytest
from httpx import AsyncClient

from bulk_uploader.apicall import GetAPICall
from fake_clients import RetryTransport


@pytest.mark.asyncio
async def test_get_api_call_ok() -> None:
    url = "https://test.org/test"
    payload = {"test_key": "test"}
    async with AsyncClient(
        transport=httpx.MockTransport(lambda item: httpx.Response(200, json=payload))
    ) as client:
        getAPICall = GetAPICall(client, url=url)
        response_data = await getAPICall.content()

    assert response_data == payload


@pytest.mark.asyncio
async def test_get_api_call_failed() -> None:
    url = "https://test.org/test"
    payload = {"test_key": "test"}
    async with AsyncClient(
        transport=httpx.MockTransport(lambda item: httpx.Response(400, json=payload))
    ) as client:
        with pytest.raises(httpx.HTTPStatusError):
            getAPICall = GetAPICall(client, url=url)
            await getAPICall.content()


@pytest.mark.asyncio
async def test_get_api_call_retry_ok() -> None:
    url = "https://test.org/test"
    payload = {"test_key": "test"}
    fake_responses = [
        httpx.Response(400, json={"msg": "failed"}),
        httpx.Response(200, json=payload),
    ]
    async with AsyncClient(
        transport=RetryTransport(handler=lambda item: "", responses=fake_responses)
    ) as client:
        getAPICall = GetAPICall(client, url=url)
        response_data = await getAPICall.content()

    assert response_data == payload
