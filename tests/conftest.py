import asyncio
import gc
import os
from functools import partial

import async_timeout
import pytest
from raven import Client

from raven_aiohttp import AioHttpTransport, QueuedAioHttpTransport
from tests.fake import FakeResolver, FakeServer

asyncio.set_event_loop(None)


@pytest.fixture
def event_loop(request):
    asyncio.set_event_loop(None)

    loop = asyncio.new_event_loop()

    loop.set_debug(bool(os.environ.get('PYTHONASYNCIODEBUG')))

    request.addfinalizer(lambda: asyncio.set_event_loop(None))

    yield loop

    loop.call_soon(loop.stop)
    loop.run_forever()
    loop.close()

    gc.collect()


@pytest.fixture
def raven_client(event_loop):
    transports = []

    def do_client(fake_server, cls, *args, **kwargs):
        kwargs.setdefault('loop', event_loop)

        dsn = 'http://foo:bar@127.0.0.1:{port}/1'.format(
            port=fake_server.port,
        )

        client = Client(dsn, transport=partial(cls, *args, **kwargs))

        transport = client.remote.get_transport()
        resolver = FakeResolver(fake_server.port)
        transport._client_session._connector._resolver = resolver

        transports.append(transport)

        return client, transport

    yield do_client

    async def do_close():
        closes = [transport.close() for transport in transports]
        await asyncio.gather(*closes)

    event_loop.run_until_complete(do_close())


@pytest.fixture
def fake_server(event_loop):
    servers = []

    async def do_server(*args, **kwargs):
        kwargs.setdefault('loop', event_loop)
        server = FakeServer(*args, **kwargs)
        servers.append(server)

        await server.start()

        return server

    yield do_server

    async def do_close():
        closes = [server.close() for server in servers]
        await asyncio.gather(*closes)

    event_loop.run_until_complete(do_close())


@pytest.fixture
def wait(event_loop):
    async def do_wait(transport, timeout=1):
        if isinstance(transport, QueuedAioHttpTransport):
            coro = transport._queue.join()
        elif isinstance(transport, AioHttpTransport):
            coro = asyncio.gather(*transport._tasks)
        else:
            raise NotImplementedError

        with async_timeout.timeout(timeout):
            await coro

    return do_wait
