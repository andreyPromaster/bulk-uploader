import asyncio
from typing import Any, Iterable


class AsyncQueue:
    def __init__(self, maxsize: int = 3):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._waiting_consumers: set[Any] = set()
        self._waiting_producers: set[Any] = set()

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
            waiter: asyncio.Future = asyncio.Future()
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
