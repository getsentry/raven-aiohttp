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

    async def resolve(self, host, port=0, family=socket.AF_INET):
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

    def __init__(self, *, side_effect=None, loop):
        self.loop = loop

        if side_effect is None:
            side_effect = {
                'status': 200,
            }

        self._side_effect = side_effect
        self._slop_factor = 0

        self.app = web.Application(loop=loop)
        self.setup_routes()

        self.port = unused_port()

        self.hits = defaultdict(lambda: 0)

    @property
    def side_effect(self):
        return self._side_effect

    def _get_slop_factor(self):
        return self._slop_factor

    def _set_slop_factor(self, value):
        self._slop_factor = value

    slop_factor = property(_get_slop_factor, _set_slop_factor)

    async def start(self):
        self.handler = self.app.make_handler(loop=self.loop)
        self.server = await self.loop.create_server(
            self.handler,
            self.host,
            self.port,
        )

    def setup_routes(self):
        self.app.router.add_post('/api/1/store/', self.store)

    async def store(self, request):
        await asyncio.sleep(self.slop_factor)

        self.hits[self.side_effect['status']] += 1
        return web.Response(**self.side_effect)

    async def close(self):
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()

        if self.app is not None:
            await self.app.shutdown()

        if self.handler is not None:
            await self.handler.shutdown()

        if self.app is not None:
            await self.app.cleanup()
