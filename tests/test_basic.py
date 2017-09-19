import asyncio

import pytest

from raven_aiohttp import AioHttpTransport, QueuedAioHttpTransport

pytestmark = pytest.mark.asyncio


@asyncio.coroutine
def test_basic_fire_and_forget(fake_server, raven_client, wait):
    server = yield from fake_server()

    client, transport = raven_client(server, AioHttpTransport)

    try:
        1 / 0
    except ZeroDivisionError:
        client.captureException()

    yield from wait(transport)

    assert server.hits[200] == 1


@asyncio.coroutine
def test_basic_queue(fake_server, raven_client, wait):
    server = yield from fake_server()

    client, transport = raven_client(server, QueuedAioHttpTransport)

    try:
        1 / 0
    except ZeroDivisionError:
        client.captureException()

    yield from wait(transport)

    assert server.hits[200] == 1
