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


class AioHttpTransport(AsyncTransport, HTTPTransport):
    def __init__(self, parsed_url, *, verify_ssl=True, resolve=True,
                 timeout=defaults.TIMEOUT,
                 keepalive=True, family=socket.AF_INET, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self._loop = loop

        super().__init__(parsed_url, timeout, verify_ssl)

        if keepalive:
            self._connector = aiohttp.TCPConnector(verify_ssl=verify_ssl,
                                                   resolve=resolve,
                                                   family=family,
                                                   loop=loop)
        else:
            self._connector = None

    def async_send(self, data, headers, success_cb, failure_cb):
        @asyncio.coroutine
        def f():
            try:
                resp = yield from asyncio.wait_for(
                    aiohttp.request('POST',
                                    self._url, data=data,
                                    headers=headers,
                                    connector=self._connector,
                                    loop=self._loop),
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

        asyncio.async(f(), loop=self._loop)
