=============
raven-aiohttp
=============

A transport for `raven-python <https://github.com/getsentry/raven-python>`_ which supports Python 3's asyncio interface.

Requirements
============

- `raven-python>=5.4.0`
- `python>=3.4.2`
- `aiohttp>=2.0`

Usage
=====

`raven-aiohttp` ships 2 asyncio based transports for `raven.Client`

AioHttpTransport
----------------

All messages to the sentry server will be produced by "Fire And Forget"

Each new message spawns it owns `asyncio.Task`, amount of them is not limited

.. code-block:: python

    import asyncio

    from raven import Client
    from raven_aiohttp import AioHttpTransport

    client = Client(transport=AioHttpTransport)

    try:
        1 / 0
    except ZeroDivisionError:
        client.captureException()

    # graceful shutdown waits until all pending messages are send

    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.remote.get_transport().close())


QueuedAioHttpTransport
----------------------

All messages to the sentry server will be produced by queue system

When transport is created it spawns limited amount of `asyncio.Task`
which sends messages one by one from internal `asyncio.Queue`

.. code-block:: python

    import asyncio
    from functols import partial

    from raven import Client
    from raven_aiohttp import QueuedAioHttpTransport

    client = Client(transport=partial(QueuedAioHttpTransport, workers=5, qsize=1000))

    try:
        1 / 0
    except ZeroDivisionError:
        client.captureException()

    # graceful shutdown waits until internal queue is empty

    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.remote.get_transport().close())
