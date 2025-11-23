import httpx


class RetryTransport(httpx.MockTransport):
    def __init__(self, handler, responses=None):
        super().__init__(handler)
        self.attempt = 0
        self.responses = responses

    async def handle_async_request(self, request):
        resp = self.responses[self.attempt]
        self.attempt += 1
        return resp
