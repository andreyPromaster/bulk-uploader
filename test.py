import asyncio
from datetime import timedelta
import logging
from bulk_uploader.manager import (
    UploadedData,
    Ratelimit,
)
from bulk_uploader.store import ListStore
from bulk_uploader.apicall import GetAPICall
from bulk_uploader.iterators import loading_urls, id_iterator

# Rotating files, save into files, db
# Sending some data to server post requests
# logging
# tests
# getting filesa
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


store = ListStore()
data = UploadedData(
    store,
    GetAPICall,
    "https://jsonplaceholder.typicode.com",
    loading_urls("https://jsonplaceholder.typicode.com/comments", id_iterator(1, 20)),
    rate_limit=Ratelimit(5, timedelta(seconds=1)),
)

asyncio.run(data.run())
print(store.saved_data())


# p = Producer(
#     requests=3,
#     url_maker=loading_urls(
#         "https://jsonplaceholder.typicode.com/comments", id_iterator(1, 40)
#     ),
# )


# import asyncio
# import random
# import time


# async def worker(name, queue):
#     while True:
#         # Get a "work item" out of the queue.
#         sleep_for = await queue.get()

#         # Sleep for the "sleep_for" seconds.
#         await asyncio.sleep(sleep_for)

#         # Notify the queue that the "work item" has been processed.
#         queue.task_done()

#         print(f"{name} has slept for {sleep_for:.2f} seconds")


# async def main():
#     # Create a queue that we will use to store our "workload".
#     queue = asyncio.Queue()

#     # Generate random timings and put them into the queue.
#     total_sleep_time = 0
#     for _ in range(20):
#         sleep_for = random.uniform(0.05, 1.0)
#         total_sleep_time += sleep_for
#         queue.put_nowait(sleep_for)

#     # Create three worker tasks to process the queue concurrently.
#     tasks = []
#     for i in range(3):
#         task = asyncio.create_task(worker(f"worker-{i}", queue))
#         tasks.append(task)

#     # Wait until the queue is fully processed.
#     started_at = time.monotonic()
#     await queue.join()
#     total_slept_for = time.monotonic() - started_at

#     # Cancel our worker tasks.
#     for task in tasks:
#         task.cancel()
#     # Wait until all worker tasks are cancelled.
#     await asyncio.gather(*tasks, return_exceptions=True)

#     print("====")
#     print(f"3 workers slept in parallel for {total_slept_for:.2f} seconds")
#     print(f"total expected sleep time: {total_sleep_time:.2f} seconds")


# asyncio.run(main())
