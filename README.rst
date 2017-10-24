.. raw:: html

    <p align="center">

.. image:: https://sentry-brand.storage.googleapis.com/sentry-logo-black.png
    :target: https://sentry.io
    :align: center
    :width: 116
    :alt: Sentry website

.. raw:: html

    </p>

===========================================================
Raven-Aiohttp - Asyncio Transport for the Sentry Python SDK
===========================================================

.. image:: https://img.shields.io/pypi/v/raven-aiohttp.svg
    :target: https://pypi.python.org/pypi/raven-aiohttp
    :alt: PyPi page link -- version

.. image:: https://travis-ci.org/getsentry/raven-aiohttp.svg?branch=master
    :target: https://travis-ci.org/getsentry/raven-aiohttp

.. image:: https://img.shields.io/pypi/l/raven-aiohttp.svg
    :target: https://pypi.python.org/pypi/raven-aiohttp
    :alt: PyPi page link -- BSD licence

.. image:: https://img.shields.io/pypi/pyversions/raven-aiohttp.svg
    :target: https://pypi.python.org/pypi/raven-aiohttp
    :alt: PyPi page link -- Python versions


A transport for the `Sentry Python SDK`_ which supports Python 3's asyncio interface.
For more information about Sentry and the python SDK, see our `Python Documentation`_ for framework integrations
and other goodies.

Requirements
============

- `raven-python>=5.4.0`
- `python>=3.4.2`
- `aiohttp>=2.0`

Usage
=====

`raven-aiohttp` ships two asyncio based transports for `raven.Client`: `AioHttpTransport` and `QueuedAioHttpTransport`.

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
    from functools import partial

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



Resources
=========

* `Sentry`_
* `Python Documentation`_
* `Issue Tracker`_
* `IRC Channel`_ (irc.freenode.net, #sentry)

.. _Sentry: https://getsentry.com/
.. _Sentry Python SDK: https://github.com/getsentry/raven-python
.. _Python Documentation: https://docs.getsentry.com/hosted/clients/python/
.. _Issue Tracker: https://github.com/getsentry/raven-aiohttp/issues
.. _IRC Channel: irc://irc.freenode.net/sentry


