import asyncio
import httpx
from apicall import GetAPICall
from interfaces import APICall, Store, Urls
from iterators import loading_urls, get_next_comment

from store import ListStore

# Rotating files, save into files, db
# Sending some data to server post requests
# logging
# tests
# getting filesa


class UploadedData:
    def __init__(self, store: Store, urls: Urls, api_call_factory: APICall, auth: httpx.Auth | None = None):
        self.store = store
        self.urls = urls
        self.api_call_factory = api_call_factory
        self.auth = auth 

    async def handle_chunk(self, client: httpx.AsyncClient):
        for url in self.urls:
            data = await self.api_call_factory(url).content(client)
            self.store.add(data)

    async def run(self):
        async with httpx.AsyncClient(auth=self.auth) as client:
            pending = [
                asyncio.create_task(self.handle_chunk(client)),
                asyncio.create_task(self.handle_chunk(client)),
            ]

            while pending:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                print(f'Done task count: {len(done)}')
                print(f'Pending task count: {len(pending)}')
                for done_task in done:
                    print(await done_task)



data = UploadedData(ListStore(), 
                    loading_urls('https://jsonplaceholder.typicode.com/comments', get_next_comment(10,15)), 
                    api_call_factory=GetAPICall)
asyncio.run(data.run())
+print(data.store.saved_data())
