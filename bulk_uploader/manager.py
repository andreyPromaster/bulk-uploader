import asyncio
import functools
import logging
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Iterable

import httpx

from .async_queue import AsyncQueue
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
        url_maker: Iterable,
        rate_limit: Ratelimit | None = None,
    ):
        self.store = store
        self.api_call_factory = api_call_factory
        self.url_maker = url_maker
        self._q = (
            AsyncQueue(maxsize=rate_limit.num_requests)
            if rate_limit is not None
            else AsyncQueue()
        )
        self.rate_limit = rate_limit

    async def save_chunks(self, client: httpx.AsyncClient, url: str):
        logger.debug(f"Start processing chunk - {url}")
        data = await self.api_call_factory(client, url).content()
        self.store.add(data)
        self._q.task_done()
        logger.debug(f"Finish processing chunk - {url}")

    async def call_maker(self, client):
        tasks = []
        while True:
            url = await self._q.get()
            task = asyncio.create_task(self.save_chunks(client, url))
            task.add_done_callback(functools.partial(_handle_task_result, q=self._q))
            tasks.append(task)

    async def url_gen(self):
        """Control rate limits"""
        logger.debug("Start queue")
        if self.rate_limit is None:
            for item in self.url_maker:
                logger.debug(f"Put item to queue - {item}")
                await self._q.put(item)
        else:
            items = []
            for item in self.url_maker:
                items.append(item)
                if len(items) >= self.rate_limit.num_requests:
                    logger.debug(f"Put items to queue - {items}")
                    self._q.batch_put(items)
                    items.clear()
                    await asyncio.sleep(self.rate_limit.period.total_seconds())
            if items:
                logger.debug(f"Put items to queue - {items}")
                self._q.batch_put(items)

        logger.debug("End queue")

    async def run(self, *args, **kwargs):
        async with httpx.AsyncClient(*args, **kwargs) as client:
            asyncio.create_task(self.call_maker(client))
            await asyncio.create_task(self.url_gen())
            await self._q.join()
