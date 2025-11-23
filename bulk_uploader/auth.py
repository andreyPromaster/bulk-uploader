import httpx


class HeaderAuth(httpx.Auth):
    def __init__(self, header_name: str, token: str):
        self.token = token
        self.header_name = header_name

    def auth_flow(self, request: httpx.Request):
        # Send the request, with a custom header.
        request.headers[self.header_name] = self.token
        yield request


class QueryParamsAuth(httpx.Auth):
    def __init__(self, query_string: str, token: str):
        self.token = token
        self.query_string = query_string

    def auth_flow(self, request: httpx.Request):
        # Send the request, with a custom header.
        request.params[self.query_string] = self.token
        yield request