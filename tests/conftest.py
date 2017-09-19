import asyncio
import gc
from functools import partial

import async_timeout
import pytest
from raven import Client

from tests.fake import FakeResolver, FakeServer


@pytest.fixture
def event_loop(request):
    loop = asyncio.new_event_loop()

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

        dsn = 'http://foo:bar@127.0.01:{port}/1'.format(
            port=fake_server.port,
        )

        client = Client(dsn, transport=partial(cls, *args, **kwargs))

        transport = client.remote.get_transport()
        resolver = FakeResolver(fake_server.port)
        transport._client_session._connector._resolver = resolver

        transports.append(transport)

        return client, transport

    yield do_client

    @asyncio.coroutine
    def do_close():
        closes = [transport.close(timeout=0) for transport in transports]
        yield from asyncio.gather(*closes, loop=event_loop)

    event_loop.run_until_complete(do_close())


@pytest.fixture
def fake_server(event_loop):
    servers = []

    @asyncio.coroutine
    def do_server(*args, **kwargs):
        kwargs.setdefault('loop', event_loop)
        server = FakeServer(*args, **kwargs)
        servers.append(server)

        yield from server.start()

        return server

    yield do_server

    @asyncio.coroutine
    def do_close():
        closes = [server.close() for server in servers]
        yield from asyncio.gather(*closes, loop=event_loop)

    event_loop.run_until_complete(do_close())


@pytest.fixture
def wait(event_loop):
    @asyncio.coroutine
    def do_wait(transport, timeout=1):
        if transport._background_workers:
            coro = transport._queue.join()
        else:
            coro = asyncio.gather(*transport._tasks, loop=event_loop)

        with async_timeout.timeout(timeout, loop=event_loop):
            yield from coro

    return do_wait
