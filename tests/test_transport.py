import asyncio
import logging
from functools import partial
from unittest import mock

import aiohttp
import pytest

from raven_aiohttp import AioHttpTransport
from tests.utils import Logger

pytestmark = pytest.mark.asyncio


@asyncio.coroutine
def test_basic(fake_server, raven_client, wait):
    server = yield from fake_server()

    client, transport = raven_client(server, AioHttpTransport)

    try:
        1 / 0
    except ZeroDivisionError:
        client.captureException()

    yield from wait(transport)

    assert server.hits[200] == 1


@asyncio.coroutine
def test_custom_client_session(fake_server, raven_client, wait):
    server = yield from fake_server()

    session = aiohttp.ClientSession()
    client, transport = raven_client(server, partial(AioHttpTransport, client_session=session))

    try:
        1 / 0
    except ZeroDivisionError:
        client.captureException()

    yield from wait(transport)

    assert server.hits[200] == 1


@asyncio.coroutine
def test_close_timeout(fake_server, raven_client):
    server = yield from fake_server()
    server.slop_factor = 100

    client, transport = raven_client(server, AioHttpTransport)

    try:
        1 / 0
    except ZeroDivisionError:
        client.captureException()

    yield from transport.close(timeout=0)

    assert server.hits[200] == 0


@asyncio.coroutine
def test_rate_limit(fake_server, raven_client, wait):
    server = yield from fake_server()
    server.side_effect['status'] = 429

    with Logger('sentry.errors', level=logging.ERROR) as log:
        client, transport = raven_client(server, AioHttpTransport)

        try:
            1 / 0
        except ZeroDivisionError:
            client.captureException()

        yield from wait(transport)

        assert server.hits[429] == 1

    msg = 'Sentry responded with an API error: RateLimited(None)'
    assert log.msgs[0] == msg


@asyncio.coroutine
def test_rate_limit_retry_after(fake_server, raven_client, wait):
    server = yield from fake_server()
    server.side_effect['status'] = 429

    server.side_effect['headers'] = {'Retry-After': '1'}

    with Logger('sentry.errors', level=logging.ERROR) as log:
        client, transport = raven_client(server, AioHttpTransport)

        try:
            1 / 0
        except ZeroDivisionError:
            client.captureException()

        yield from wait(transport)

        assert server.hits[429] == 1

    msg = 'Sentry responded with an API error: RateLimited(None)'
    assert log.msgs[0] == msg


@asyncio.coroutine
def test_status_500(fake_server, raven_client, wait):
    server = yield from fake_server()
    server.side_effect['status'] = 500

    with Logger('sentry.errors', level=logging.ERROR) as log:
        client, transport = raven_client(server, AioHttpTransport)

        try:
            1 / 0
        except ZeroDivisionError:
            client.captureException()

        yield from wait(transport)

        assert server.hits[500] == 1

    msg = 'Sentry responded with an API error: APIError(None)'
    assert log.msgs[0] == msg


@asyncio.coroutine
def test_cancelled_error(fake_server, raven_client, wait):
    server = yield from fake_server()

    with mock.patch(
        'aiohttp.ClientSession.post',
        side_effect=asyncio.CancelledError,
    ):
        with Logger('sentry.errors', level=logging.ERROR) as log:
            client, transport = raven_client(server, AioHttpTransport)

            try:
                1 / 0
            except ZeroDivisionError:
                client.captureException()

            with pytest.raises(asyncio.CancelledError):
                yield from wait(transport)

            assert server.hits[200] == 0


@asyncio.coroutine
def test_async_send_when_closed(fake_server, raven_client):
    server = yield from fake_server()

    with Logger('sentry.errors', level=logging.ERROR) as log:
        client, transport = raven_client(server, AioHttpTransport)

        close = transport.close()

        try:
            1 / 0
        except ZeroDivisionError:
            client.captureException()

        assert server.hits[200] == 0

    assert log.msgs[0].startswith(
        'Sentry responded with an error: AioHttpTransport is closed')

    yield from close
