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

try:
    from asyncio import ensure_future
except ImportError:
    ensure_future = asyncio.async


class AioHttpTransport(AsyncTransport, HTTPTransport):
    def __init__(self, parsed_url, *, verify_ssl=True, resolve=True,
                 timeout=defaults.TIMEOUT,
                 keepalive=True, family=socket.AF_INET, loop=None):
        self._resolve = resolve
        self._keepalive = keepalive
        self._family = family
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop

        super().__init__(parsed_url, timeout, verify_ssl)
        self._client_session = None

    @property
    def resolve(self):
        return self._resolve

    @property
    def keepalive(self):
        return self._keepalive

    @property
    def family(self):
        return self._family

    def client_session(self):
        if not self.keepalive or \
                (self._client_session is None or self._client_session.closed):
            connector = aiohttp.TCPConnector(verify_ssl=self.verify_ssl,
                                             resolve=self.resolve,
                                             family=self.family,
                                             loop=self._loop)
            self._client_session = aiohttp.ClientSession(connector=connector,
                                                         loop=self._loop)
        return self._client_session

    def async_send(self, data, headers, success_cb, failure_cb):
        @asyncio.coroutine
        def f():
            session = self.client_session()
            try:
                resp = yield from asyncio.wait_for(
                    session.post(self._url,
                                 data=data,
                                 compress=False,
                                 headers=headers),
                    self.timeout,
                    loop=self._loop)
                yield from resp.release()
                code = resp.status
                if code != 200:
                    msg = resp.headers.get('x-sentry-error')
                    if code == 429:
                        try:
                            retry_after = int(resp.headers.get('retry-after'))
                        except (ValueError, TypeError):
                            retry_after = 0
                        failure_cb(RateLimited(msg, retry_after))
                    else:
                        failure_cb(APIError(msg, code))
                else:
                    success_cb()
            except Exception as exc:
                failure_cb(exc)
            finally:
                if not self.keepalive:
                    yield from session.close()

        ensure_future(f(), loop=self._loop)
