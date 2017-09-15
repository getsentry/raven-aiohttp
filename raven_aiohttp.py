"""
raven_aiohttp
~~~~~~~~~~~~~

:copyright: (c) 2010-2015 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from raven.exceptions import APIError, RateLimited
from raven.transport.base import AsyncTransport
from raven.transport.http import HTTPTransport
from raven.conf import defaults

import aiohttp
import asyncio
import socket
import logging

try:
    from asyncio import ensure_future
except ImportError:
    ensure_future = getattr(asyncio, 'async')

import async_timeout
try:
    from raven.transport.base import has_newstyle_transports
except ImportError:
    has_newstyle_transports = False


logger = logging.getLogger('sentry.errors')


class AioHttpTransport(AsyncTransport, HTTPTransport):
    QUEUE_LIMIT = 1000
    WORKERS = 10

    def __init__(self, parsed_url=None, *, verify_ssl=True, resolve=True,
                 timeout=defaults.TIMEOUT,
                 keepalive=True, family=socket.AF_INET, loop=None):
        self._resolve = resolve
        self._keepalive = keepalive
        self._family = family
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop

        if has_newstyle_transports:
            if parsed_url is not None:
                raise TypeError('Transport accepts no URLs for this version '
                                'of raven.')
            super().__init__(timeout, verify_ssl)
        else:
            super().__init__(parsed_url, timeout, verify_ssl)

        if self.keepalive:
            self._client_session = self._client_session_factory()

        self._closing = False
        self._queue = asyncio.Queue(self.QUEUE_LIMIT)
        self._workers = set()
        for _ in range(self.WORKERS):
            worker = ensure_future(self._worker(), loop=self._loop)
            self._workers.add(worker)
            worker.add_done_callback(self._workers.remove)

    @property
    def resolve(self):
        return self._resolve

    @property
    def keepalive(self):
        return self._keepalive

    @property
    def family(self):
        return self._family

    def _client_session_factory(self):
        # by default aiohttp.TCPConnector deadly caches dns
        connector = aiohttp.TCPConnector(verify_ssl=self.verify_ssl,
                                         resolve=self.resolve,
                                         family=self.family,
                                         use_dns_cache=False,
                                         loop=self._loop)
        return aiohttp.ClientSession(connector=connector,
                                     loop=self._loop)

    def _queue_put(self, data):
        try:
            self._queue.put_nowait(data)
        except asyncio.QueueFull as exc:
            logger.error('AioHttpTransport._queue was throttled', exc_info=exc)
            # throw last oldest message in queue and put new one
            self._queue.get_nowait()
            self._queue.put_nowait(data)

    @asyncio.coroutine
    def close(self, timeout=None):
        self._closing = True

        self._queue_put(...)

        try:
            with async_timeout.timeout(timeout, loop=self._loop):
                yield from asyncio.gather(*self._workers, loop=self._loop)

            assert len(self._workers) == 0
            assert self._queue.get_nowait() == ...
        finally:
            if self.keepalive:
                yield from self._client_session.close()

    @asyncio.coroutine
    def _worker(self):
        while True:
            data = yield from self._queue.get()

            if data is ...:
                self._queue_put(...)
                break

            url, data, headers, success_cb, failure_cb = data

            yield from self.__async_send(url, data, headers, success_cb,
                                         failure_cb)

    @asyncio.coroutine
    def __async_send(self, url, data, headers, success_cb, failure_cb):
        if self.keepalive:
            session = self._client_session
        else:
            session = self._client_session_factory()

        resp = None
        try:
            with async_timeout.timeout(self.timeout, loop=self._loop):
                # timeout=None disables built-int aiohttp timeout
                resp = yield from session.post(url, data=data, compress=False,
                                               headers=headers, timeout=None)

                code = resp.status
                if code != 200:
                    msg = resp.headers.get('x-sentry-error')
                    if code == 429:
                        try:
                            retry_after = resp.headers.get('retry-after')
                            retry_after = int(retry_after)
                        except (ValueError, TypeError):
                            retry_after = 0
                        failure_cb(RateLimited(msg, retry_after))
                    else:
                        failure_cb(APIError(msg, code))
                else:
                    success_cb()
        except asyncio.CancelledError:
            # do not mute asyncio.CancelledError
            raise
        except Exception as exc:
            failure_cb(exc)
        finally:
            if resp is not None:
                resp.release()
            if not self.keepalive:
                yield from session.close()

    def async_send(self, url, data, headers, success_cb, failure_cb):
        if self._closing:
            raise RuntimeError('AioHttpTransport is closing')

        data = url, data, headers, success_cb, failure_cb

        self._queue_put(data)

    if not has_newstyle_transports:
        _async_send = async_send

        def async_send(self, *args, **kwargs):
            return self._async_send(self._url, *args, **kwargs)
