import asyncio
import socket
from collections import defaultdict

from aiohttp import web
from aiohttp.test_utils import unused_port


class FakeResolver:

    _LOCAL_HOST = {
        0: '127.0.0.1',
        socket.AF_INET: '127.0.0.1',
        socket.AF_INET6: '::1',
    }

    def __init__(self, port):
        self.port = port

    @asyncio.coroutine
    def resolve(self, host, port=0, family=socket.AF_INET):
        return [
            {
                'hostname': host,
                'host': self._LOCAL_HOST[family],
                'port': self.port,
                'family': family,
                'proto': 0,
                'flags': socket.AI_NUMERICHOST,
            },
        ]


class FakeServer:

    app = None
    handler = None
    server = None

    host = '127.0.0.1'

    def __init__(self, *, side_effect=200, loop):
        self.loop = loop

        self.app = web.Application(loop=loop)
        self.setup_routes()

        self.port = unused_port()
        self._side_effect = side_effect

        self.hits = defaultdict(lambda: 0)

    def _get_side_effect(self):
        return self._side_effect

    def _set_side_effect(self, value):
        self._side_effect = value

    side_effect = property(_get_side_effect, _set_side_effect)

    @asyncio.coroutine
    def start(self):
        self.handler = self.app.make_handler(loop=self.loop)
        self.server = yield from self.loop.create_server(
            self.handler,
            self.host,
            self.port,
        )

    def setup_routes(self):
        self.app.router.add_post('/api/1/store/', self.store)

    @asyncio.coroutine
    def store(self, request):
        self.hits[self.side_effect] += 1
        return web.Response(status=self.side_effect)

    @asyncio.coroutine
    def close(self):
        if self.server is not None:
            self.server.close()
            yield from self.server.wait_closed()

        if self.app is not None:
            yield from self.app.shutdown()

        if self.handler is not None:
            yield from self.handler.shutdown()

        if self.app is not None:
            yield from self.app.cleanup()
