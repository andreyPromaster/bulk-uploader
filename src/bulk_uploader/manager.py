import asyncio
import httpx
from interfaces import APICall, Store, Urls


class UploadedData:
    def __init__(self, store: Store, api_call_factory: APICall, urls: Urls):
        self.store = store
        self.api_call_factory = api_call_factory
        self.urls = urls

    async def save_chunk(self, client):
        for url in self.urls:
            data = await self.api_call_factory(url).content(client)
            self.store.add(data)


class ConcurrentRequests:
    def __init__(self, uploaded_data: UploadedData, number_of_workers: int = 10, auth: httpx.Auth | None = None):
        self.number_of_workers = number_of_workers
        self.uploaded_data = uploaded_data
        self.auth = auth
    
    async def run(self):
        async with httpx.AsyncClient(auth=self.auth) as client:
            pending = [asyncio.create_task(self.uploaded_data.save_chunk(client)) for _ in range(self.number_of_workers)]

            while pending:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                # for done_task in done:
                #     await done_task
