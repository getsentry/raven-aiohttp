"""
raven_aiohttp
~~~~~~~~~~~~~

:copyright: (c) 2010-2015 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
import abc
import asyncio
import socket

import aiohttp
from raven.conf import defaults
from raven.exceptions import APIError, RateLimited
from raven.transport.base import AsyncTransport
from raven.transport.http import HTTPTransport

try:
    from asyncio import ensure_future
except ImportError:
    ensure_future = getattr(asyncio, 'async')

try:
    from raven.transport.base import has_newstyle_transports
except ImportError:
    has_newstyle_transports = False

__version__ = '0.6.0'


class AioHttpTransportBase(
    AsyncTransport,
    HTTPTransport,
    metaclass=abc.ABCMeta
):

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
        connector = aiohttp.TCPConnector(verify_ssl=self.verify_ssl,
                                         resolve=self.resolve,
                                         family=self.family,
                                         loop=self._loop)
        return aiohttp.ClientSession(connector=connector,
                                     loop=self._loop)

    @asyncio.coroutine
    def _do_send(self, url, data, headers, success_cb, failure_cb):
        if self.keepalive:
            session = self._client_session
        else:
            session = self._client_session_factory()

        resp = None

        try:
            resp = yield from session.post(
                url,
                data=data,
                compress=False,
                headers=headers,
                timeout=self.timeout
            )

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

    @abc.abstractmethod
    def _async_send(self, url, data, headers, success_cb, failure_cb):  # pragma: no cover
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def _close(self):  # pragma: no cover
        pass

    def async_send(self, url, data, headers, success_cb, failure_cb):
        if self._closing:
            failure_cb(RuntimeError(
                '{} is closed'.format(self.__class__.__name__)))
            return

        self._async_send(url, data, headers, success_cb, failure_cb)

    @asyncio.coroutine
    def _close_coro(self, *, timeout=None):
        try:
            yield from asyncio.wait_for(
                self._close(), timeout=timeout, loop=self._loop)
        except asyncio.TimeoutError:
            pass
        finally:
            if self.keepalive:
                yield from self._client_session.close()

    def close(self, *, timeout=None):
        if self._closing:
            @asyncio.coroutine
            def dummy():
                pass

            return dummy()

        self._closing = True

        return self._close_coro(timeout=timeout)

    if not has_newstyle_transports:
        oldstyle_async_send = async_send

        def async_send(self, *args, **kwargs):
            return self.oldstyle_async_send(self._url, *args, **kwargs)


class AioHttpTransport(AioHttpTransportBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._tasks = set()

    def _async_send(self, url, data, headers, success_cb, failure_cb):
        coro = self._do_send(url, data, headers, success_cb, failure_cb)

        task = ensure_future(coro, loop=self._loop)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.remove)

    @asyncio.coroutine
    def _close(self):
        yield from asyncio.gather(
            *self._tasks,
            return_exceptions=True,
            loop=self._loop
        )

        assert len(self._tasks) == 0


class QueuedAioHttpTransport(AioHttpTransportBase):

    def __init__(self, *args, workers=1, qsize=1000, **kwargs):
        super().__init__(*args, **kwargs)

        self._queue = asyncio.Queue(maxsize=qsize, loop=self._loop)

        self._workers = set()

        for _ in range(workers):
            worker = ensure_future(self._worker(), loop=self._loop)
            self._workers.add(worker)
            worker.add_done_callback(self._workers.remove)

    @asyncio.coroutine
    def _worker(self):
        while True:
            data = yield from self._queue.get()

            try:
                if data is ...:
                    self._queue.put_nowait(...)
                    break

                url, data, headers, success_cb, failure_cb = data

                yield from self._do_send(url, data, headers, success_cb,
                                         failure_cb)
            finally:
                self._queue.task_done()

    def _async_send(self, url, data, headers, success_cb, failure_cb):
        data = url, data, headers, success_cb, failure_cb

        try:
            self._queue.put_nowait(data)
        except asyncio.QueueFull as exc:
            skipped = self._queue.get_nowait()
            self._queue.task_done()

            *_, failure_cb = skipped

            failure_cb(RuntimeError(
                'QueuedAioHttpTransport internal queue is full'))

            self._queue.put_nowait(data)

    @asyncio.coroutine
    def _close(self):
        try:
            self._queue.put_nowait(...)
        except asyncio.QueueFull as exc:
            skipped = self._queue.get_nowait()
            self._queue.task_done()

            *_, failure_cb = skipped

            failure_cb(RuntimeError(
                'QueuedAioHttpTransport internal queue was full'))

            self._queue.put_nowait(...)

        yield from asyncio.gather(
            *self._workers,
            return_exceptions=True,
            loop=self._loop
        )

        assert len(self._workers) == 0
        assert self._queue.qsize() == 1
        try:
            assert self._queue.get_nowait() is ...
        finally:
            self._queue.task_done()
