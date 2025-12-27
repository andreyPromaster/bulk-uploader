# Bulk Uploader

A high-performance async tool for bulk fetching and processing data from APIs with built-in rate limiting, batching, and flexible storage options. Perfect for integration into data pipelines that need to handle large-scale API requests efficiently.

## Features

- **Async/Await Support**: Leverages Python's asyncio for concurrent requests
- **Rate Limiting**: Built-in rate limiter to respect API quotas and prevent throttling
- **Batch Processing**: Automatically batches requests for optimal throughput
- **Flexible Storage**: Pluggable storage backends (in-memory, database, file-based, etc.)
- **Custom Authentication**: Support for header-based and query parameter-based authentication
- **Error Handling**: Graceful error handling with logging support
- **Retry Policies**: Integration with tenacity for automatic retries
- **Pipeline Integration**: Easy integration into data processing pipelines

## Installation

```bash
poetry install
```

### Dependencies

- Python >= 3.10
- httpx >= 0.27.0
- tenacity >= 9.0.0

## Quick Start

### Basic Usage

```python
import asyncio
from datetime import timedelta
from bulk_uploader import (
    UploadedData,
    GetAPICall,
    ListStore,
    Ratelimit,
    loading_urls,
    id_iterator
)

# Create a store to collect results
store = ListStore()

# Define URL generator
urls = loading_urls(
    "https://api.example.com/items",
    id_iterator(1, 100)  # generates 1-99
)

# Create uploader with rate limiting
uploader = UploadedData(
    store=store,
    api_call_factory=GetAPICall,
    url_maker=urls,
    rate_limit=Ratelimit(
        num_requests=5,
        period=timedelta(seconds=1)  # 5 requests per second
    )
)

# Run the bulk upload
asyncio.run(uploader.run())

# Access collected data
results = store.saved_data()
```

## Core Components

### UploadedData

The main orchestrator class that manages the entire bulk operation.

**Parameters:**
- `store`: Storage backend implementing the `Store` protocol
- `api_call_factory`: API call implementation (e.g., `GetAPICall`)
- `url_maker`: Iterable of URLs to process
- `rate_limit`: Optional `Ratelimit` instance for controlling request rate

**Methods:**
- `async run(*args, **kwargs)`: Execute the bulk upload operation

### Ratelimit

Controls the rate at which requests are made.

**Parameters:**
- `num_requests`: Number of requests allowed in each period
- `period`: `timedelta` object specifying the time period (default: 1 second)

**Example:**
```python
# 10 requests per 2 seconds
rate_limit = Ratelimit(
    num_requests=10,
    period=timedelta(seconds=2)
)
```

### Storage Backends

#### ListStore

Simple in-memory storage using a list.

```python
from bulk_uploader import ListStore

store = ListStore()
# Process data...
results = store.saved_data()  # Returns list of all collected data
```

Create custom storage by implementing the `Store` protocol:

```python
from bulk_uploader.interfaces import Store

class DatabaseStore(Store):
    def __init__(self, db_connection):
        self.db = db_connection
    
    def add(self, data):
        """Add data to your storage backend"""
        self.db.insert(data)
    
    def saved_data(self):
        """Retrieve all saved data"""
        return self.db.fetch_all()
```

### API Call Implementations

#### GetAPICall

Performs GET requests to fetch data from URLs.

```python
from bulk_uploader import GetAPICall

uploader = UploadedData(
    store=store,
    api_call_factory=GetAPICall,
    url_maker=urls,
)
```

Create custom implementations by implementing the `APICall` protocol:

```python
from bulk_uploader.interfaces import APICall
import httpx

class PostAPICall(APICall):
    def __init__(self, client: httpx.AsyncClient, url: str, retry_policy=None):
        self.client = client
        self.url = url
        self.retry_policy = retry_policy
    
    async def content(self):
        """Fetch and return data from the URL"""
        response = await self.client.post(self.url)
        return response.json()
```

### URL Generators

#### loading_urls

Combines a base URL with an iterator of identifiers.

```python
from bulk_uploader import loading_urls, id_iterator

# Generate URLs like: https://api.example.com/items/1, /2, /3, etc.
urls = loading_urls(
    "https://api.example.com/items",
    id_iterator(1, 100)
)
```

#### id_iterator

Generates sequential integer IDs.

```python
from bulk_uploader import id_iterator

# Generate integers from 1 to 99 (step of 1)
ids = id_iterator(start=1, end=100, step=1)
```

#### days_intervals

Splits a date range into intervals, useful for time-based API pagination.

```python
from datetime import date
from bulk_uploader.iterators import days_intervals

start = date(2024, 1, 1)
end = date(2024, 12, 31)

for start_date, end_date in days_intervals(start, end, delta_days=7):
    # Process data for each week
    print(f"Processing {start_date} to {end_date}")
```

### Authentication

#### HeaderAuth

Add authentication via HTTP headers.

```python
from bulk_uploader import HeaderAuth

auth = HeaderAuth(
    header_name="Authorization",
    token="Bearer your_token_here"
)

uploader = UploadedData(
    store=store,
    api_call_factory=GetAPICall,
    url_maker=urls,
)

asyncio.run(uploader.run(auth=auth))
```

#### QueryParamsAuth

Add authentication via query parameters.

```python
from bulk_uploader import QueryParamsAuth

auth = QueryParamsAuth(
    query_string="api_key",
    token="your_api_key"
)

asyncio.run(uploader.run(auth=auth))
```

## Advanced Usage

### Pipeline Integration Example

```python
import asyncio
from datetime import date, timedelta
from bulk_uploader import (
    UploadedData,
    GetAPICall,
    ListStore,
    Ratelimit,
    loading_urls,
    HeaderAuth
)
from bulk_uploader.iterators import days_intervals

# Define pipeline
async def process_daily_data():
    # Time-based iteration for API that supports date ranges
    for start_date, end_date in days_intervals(
        date(2024, 1, 1),
        date(2024, 1, 31),
        delta_days=1
    ):
        store = ListStore()
        
        # Build URLs with date parameters
        urls = [
            f"https://api.example.com/data?start={start_date}&end={end_date}"
        ]
        
        uploader = UploadedData(
            store=store,
            api_call_factory=GetAPICall,
            url_maker=urls,
            rate_limit=Ratelimit(10, timedelta(seconds=1))
        )
        
        auth = HeaderAuth("Authorization", "Bearer token")
        await uploader.run(auth=auth)
        
        # Process results
        for item in store.saved_data():
            print(item)

# Run the pipeline
asyncio.run(process_daily_data())
```

### Custom Retry Policy

```python
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

retry_policy = AsyncRetrying(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)

# Use with custom APICall implementation
```

## Configuration

### Logging

Enable debug logging to monitor operations:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

## Testing

Run tests with pytest:

```bash
poetry run pytest tests/ -v
```

## Architecture

The tool uses an async queue-based architecture:

1. **URL Generator** (`url_gen`): Produces URLs with rate limiting
2. **Queue**: Buffers URLs respecting concurrency and rate limits
3. **API Caller** (`call_maker`): Consumes URLs and makes requests
4. **Storage**: Accumulates results

This separation allows for efficient concurrent processing while maintaining rate limit compliance.

## Performance Considerations

- **Rate Limiting**: Adjust `Ratelimit` parameters based on API quotas
- **Queue Size**: Larger batches improve throughput but use more memory
- **Concurrency**: The queue naturally throttles concurrent requests
- **Storage Backend**: Choose storage appropriate for your data volume

## Error Handling

Errors are logged but don't halt the entire operation:

```python
import logging

logger = logging.getLogger("bulk_uploader")
# Check logs for individual request failures
```

For custom error handling, implement a custom `Store` that captures error states.

## Contributing

To add new features:

1. Implement the appropriate protocol (`Store`, `APICall`, `Auth`)
2. Add tests in the `tests/` directory
3. Update this README with examples

## License

[Add your license here]

## Support

For issues and questions, please open an issue on the repository.