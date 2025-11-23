import typing

import httpx
from tenacity import AsyncRetrying


class RequestHandler(typing.Protocol):
    def process(self, client: httpx.AsyncClient):
        """Create a request to a specific API"""


class Store(typing.Protocol):
    def add(self, *args, **kwargs):
        """"""

    def saved_data(self):
        """"""


class APICall(typing.Protocol):
    def __init__(
        self,
        client: httpx.AsyncClient,
        url: str,
        retry_policy: AsyncRetrying | None = None,
    ):
        """"""

    async def content(self):
        """"""
