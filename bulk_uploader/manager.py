import asyncio
from dataclasses import dataclass, field
import functools
import logging
import random
from datetime import datetime, timedelta
from typing import Any, Iterable

import httpx

from .interfaces import APICall, Store

logger = logging.getLogger(__name__)


def _handle_task_result(task: asyncio.Task, q) -> None:
    try:
        task.result()
    except asyncio.CancelledError:
        pass
    # Task cancellation should not be logged as an error.
    # Ad the pylint ignore: we want to handle all exceptions here so that the result of the task
    # is properly logged. There is no point re-raising the exception in this callback.
    except Exception as e:  # pylint: disable=broad-except
        logger.error(e)
        q.task_done()
        task.cancel()


@dataclass
class Ratelimit:
    DEFAUL_PERIOD_SEC = 1
    num_requests: int
    period: timedelta = field(
        default_factory=lambda: timedelta(seconds=Ratelimit.DEFAUL_PERIOD_SEC)
    )


class UploadedData:
    def __init__(
        self,
        store: Store,
        api_call_factory: type[APICall],
        base_url: str,
        url_maker: Iterable,
        auth: httpx.Auth | None = None,
        rate_limit: Ratelimit | None = None,
    ):
        self.store = store
        self.api_call_factory = api_call_factory
        self.base_url = base_url
        self.url_maker = url_maker
        self.auth = auth
        self.q = (
            AsyncQueue(maxsize=rate_limit.num_requests)
            if rate_limit is not None
            else AsyncQueue()
        )
        self.rate_limit = rate_limit

    async def save_chunks(self, client: httpx.AsyncClient, url: str):
        logger.debug(f"Start processing chunk - {url}")
        data = await self.api_call_factory(client, url).content()
        self.store.add(data)
        self.q.task_done()
        logger.debug(f"Finish processing chunk - {url}")

    async def call_maker(self, client):
        tasks = []
        while True:
            url = await self.q.get()
            task = asyncio.create_task(self.save_chunks(client, url))
            task.add_done_callback(functools.partial(_handle_task_result, q=self.q))
            tasks.append(task)

    async def url_gen(self):
        """Control rate limits"""
        logger.debug("Start queue")
        if self.rate_limit is None:
            for item in self.url_maker:
                logger.debug(f"Put item to queue - {item}")
                await self.q.put(item)
        else:
            items = []
            for item in self.url_maker:
                items.append(item)
                if len(items) >= self.rate_limit.num_requests:
                    logger.debug(f"Put items to queue - {items}")
                    self.q.batch_put(items)
                    items.clear()
                    await asyncio.sleep(self.rate_limit.period.total_seconds())
            if items:
                logger.debug(f"Put items to queue - {items}")
                self.q.batch_put(items)

        logger.debug("End queue")

    async def run(self):
        async with httpx.AsyncClient(auth=self.auth, base_url=self.base_url) as client:
            asyncio.create_task(self.call_maker(client))
            await asyncio.create_task(self.url_gen())
            await self.q.join()


class AsyncQueue:
    def __init__(self, maxsize: int = 3):
        self._queue = asyncio.Queue(maxsize=maxsize)
        self._waiting_consumers = set()
        self._waiting_producers = set()

    async def put(self, item: Any) -> None:
        await self._queue.put(item)
        if self._waiting_consumers:
            waiter = self._waiting_consumers.pop()
            waiter.set_result(True)

    def batch_put(self, items: Iterable[Any]) -> None:
        for item in items:
            self._queue.put_nowait(item)

        while self._waiting_consumers:
            waiter = self._waiting_consumers.pop()
            waiter.set_result(True)

    async def get(self) -> Any:
        if self._queue.empty():
            # Create a future to wait for new items
            waiter = asyncio.Future()
            self._waiting_consumers.add(waiter)
            await waiter
        return await self._queue.get()

    def empty(self) -> bool:
        return self._queue.empty()

    def qsize(self) -> int:
        return self._queue.qsize()

    async def join(self) -> None:
        await self._queue.join()

    def task_done(self) -> None:
        self._queue.task_done()
