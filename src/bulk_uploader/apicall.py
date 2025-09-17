import httpx
from tenacity import AsyncRetrying, RetryError, stop_after_attempt

from interfaces import APICall


class GetAPICall(APICall):
    def __init__(self, url: str, retry_policy: AsyncRetrying | None=None):
        self.url = url
        self.retry_policy = AsyncRetrying(stop=stop_after_attempt(3)) if retry_policy is None else retry_policy
    
    async def content(self, client: httpx.AsyncClient):
        try:
            async for attempt in self.retry_policy:
                with attempt:
                    resp = await client.get(self.url)
                    return resp.raise_for_status().json()
        except RetryError:
            pass

        