import asyncio
import random
import httpx
from tenacity import AsyncRetrying, RetryError, stop_after_attempt

from .interfaces import APICall


class GetAPICall(APICall):
    def __init__(
        self,
        client: httpx.AsyncClient,
        url: str,
        retry_policy: AsyncRetrying | None = None,
    ):
        self.url = url
        self.retry_policy = (
            AsyncRetrying(stop=stop_after_attempt(3))
            if retry_policy is None
            else retry_policy
        )
        self.client = client

    async def content(self):
        try:
            async for attempt in self.retry_policy:
                with attempt:
                    resp = await self.client.get(self.url)
                    await asyncio.sleep(random.random() * 2)
                    resp.raise_for_status()
                    return resp.json()
        except RetryError as e:
            raise e.reraise()
