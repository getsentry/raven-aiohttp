import asyncio
import logging
from functools import partial
from unittest import mock

import pytest

from raven_aiohttp import QueuedAioHttpTransport
from tests.utils import Logger

pytestmark = pytest.mark.asyncio


async def test_basic(fake_server, raven_client, wait):
    server = await fake_server()

    client, transport = raven_client(server, QueuedAioHttpTransport)

    try:
        1 / 0
    except ZeroDivisionError:
        client.captureException()

    await wait(transport)

    assert server.hits[200] == 1


async def test_no_keepalive(fake_server, raven_client, wait):
    transport = QueuedAioHttpTransport(keepalive=False)
    assert not hasattr(transport, '_client_session')
    await transport.close()

    server = await fake_server()

    client, transport = raven_client(server, QueuedAioHttpTransport)
    transport._keepalive = False
    session = transport._client_session

    def _client_session_factory():
        return session

    with mock.patch(
        'raven_aiohttp.QueuedAioHttpTransport._client_session_factory',
        side_effect=_client_session_factory,
    ):
        try:
            1 / 0
        except ZeroDivisionError:
            client.captureException()

        await wait(transport)

        assert session.closed

        assert server.hits[200] == 1


async def test_close_timeout(fake_server, raven_client):
    server = await fake_server()
    server.slop_factor = 100

    client, transport = raven_client(server, QueuedAioHttpTransport)

    try:
        1 / 0
    except ZeroDivisionError:
        client.captureException()

    await transport.close(timeout=0)

    assert server.hits[200] == 0


async def test_rate_limit(fake_server, raven_client, wait):
    server = await fake_server()
    server.side_effect['status'] = 429

    with Logger('sentry.errors', level=logging.ERROR) as log:
        client, transport = raven_client(server, QueuedAioHttpTransport)

        try:
            1 / 0
        except ZeroDivisionError:
            client.captureException()

        await wait(transport)

        assert server.hits[429] == 1

    msg = 'Sentry responded with an API error: RateLimited(None)'
    assert log.msgs[0] == msg


async def test_rate_limit_retry_after(fake_server, raven_client, wait):
    server = await fake_server()
    server.side_effect['status'] = 429

    server.side_effect['headers'] = {'Retry-After': '1'}

    with Logger('sentry.errors', level=logging.ERROR) as log:
        client, transport = raven_client(server, QueuedAioHttpTransport)

        try:
            1 / 0
        except ZeroDivisionError:
            client.captureException()

        await wait(transport)

        assert server.hits[429] == 1

    msg = 'Sentry responded with an API error: RateLimited(None)'
    assert log.msgs[0] == msg


async def test_status_500(fake_server, raven_client, wait):
    server = await fake_server()
    server.side_effect['status'] = 500

    with Logger('sentry.errors', level=logging.ERROR) as log:
        client, transport = raven_client(server, QueuedAioHttpTransport)

        try:
            1 / 0
        except ZeroDivisionError:
            client.captureException()

        await wait(transport)

        assert server.hits[500] == 1

    msg = 'Sentry responded with an API error: APIError(None)'
    assert log.msgs[0] == msg


async def test_cancelled_error(event_loop, fake_server, raven_client, wait):
    server = await fake_server()

    with mock.patch(
        'aiohttp.ClientSession.post',
        side_effect=asyncio.CancelledError,
    ):
        client, transport = raven_client(server, QueuedAioHttpTransport)

        try:
            1 / 0
        except ZeroDivisionError:
            client.captureException()

        await wait(transport)

        assert server.hits[200] == 0

        with pytest.raises(asyncio.CancelledError):
            await asyncio.gather(*transport._workers)


async def test_async_send_when_closed(fake_server, raven_client):
    server = await fake_server()

    with Logger('sentry.errors', level=logging.ERROR) as log:
        client, transport = raven_client(server, QueuedAioHttpTransport)

        close = transport.close()

        try:
            1 / 0
        except ZeroDivisionError:
            client.captureException()

        assert server.hits[200] == 0

    assert log.msgs[0].startswith(
        'Sentry responded with an error: QueuedAioHttpTransport is closed')

    await close


async def test_async_send_queue_full(fake_server, raven_client, wait):
    server = await fake_server()

    with Logger('sentry.errors', level=logging.ERROR) as log:
        transport = partial(QueuedAioHttpTransport, qsize=1)

        client, transport = raven_client(server, transport)

        try:
            1 / 0
        except ZeroDivisionError:
            client.captureException()

        try:
            1 / 0
        except ZeroDivisionError:
            client.captureException()

        await wait(transport)

        assert server.hits[200] == 1

    msg = 'Sentry responded with an error: ' \
          'QueuedAioHttpTransport internal queue is full'
    assert log.msgs[0].startswith(msg)


async def test_async_send_queue_full_close(fake_server, raven_client):
    server = await fake_server()

    with Logger('sentry.errors', level=logging.ERROR) as log:
        transport = partial(QueuedAioHttpTransport, qsize=1)

        client, transport = raven_client(server, transport)

        try:
            1 / 0
        except ZeroDivisionError:
            client.captureException()

        await transport.close()

        assert server.hits[200] == 0

    msg = 'Sentry responded with an error: ' \
          'QueuedAioHttpTransport internal queue was full'
    assert log.msgs[0].startswith(msg)
