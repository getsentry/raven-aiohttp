import asyncio

import pytest

from raven_aiohttp import AioHttpTransport, QueuedAioHttpTransport


transports = [QueuedAioHttpTransport, AioHttpTransport]


@pytest.mark.parametrize('transport', transports)
def test_loop_is_none(transport):
    with pytest.raises(RuntimeError):
        transport()


@pytest.mark.parametrize('transport', transports)
def test_explicit_loop(transport, event_loop):
    _transport = transport(loop=event_loop)

    assert _transport._loop is event_loop

    event_loop.run_until_complete(_transport.close())


@pytest.mark.parametrize('transport', transports)
def test_global_loop(transport, event_loop):
    asyncio.set_event_loop(event_loop)

    _transport = transport()

    assert _transport._loop is event_loop

    event_loop.run_until_complete(_transport.close())


@pytest.mark.parametrize('transport', transports)
def test_has_newstyle_transports_parsed_url(transport, event_loop):
    with pytest.raises(TypeError):
        transport('1', loop=event_loop)


@pytest.mark.parametrize('transport', transports)
def test_transport_closed_twice(transport, event_loop, mocker):
    _transport = transport(loop=event_loop)

    event_loop.run_until_complete(_transport.close())

    mocker.spy(_transport, '_close_coro')

    event_loop.run_until_complete(_transport.close())

    assert _transport._close_coro.call_count == 0
