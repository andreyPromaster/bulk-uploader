import asyncio
from manager import ConcurrentRequests, UploadedData
from store import ListStore
from apicall import GetAPICall
from iterators import loading_urls, get_next_comment

# Rotating files, save into files, db
# Sending some data to server post requests
# logging
# tests
# getting filesa


store = ListStore()
data = UploadedData(store, 
                    GetAPICall,
                    loading_urls('https://jsonplaceholder.typicode.com/comments', get_next_comment(1,40)), 
                    )
reqs = ConcurrentRequests(data)

asyncio.run(reqs.run())
print(store.saved_data())