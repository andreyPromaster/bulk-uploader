import typing

import httpx

class RequestHandler(typing.Protocol):
    def process(self, client: httpx.AsyncClient):
        """Create a request to a specific API """


class Store(typing.Protocol):
    def add(self, *args, **kwargs):
        """"""

class Urls(typing.Protocol):
    def next_url(self):
        """"""

class APICall(typing.Protocol):
    async def content(self, client: httpx.AsyncClient):
        """"""