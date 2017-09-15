# raven-aiohttp

A transport for [raven-python](https://github.com/getsentry/raven-python) which supports Python 3's asyncio interface.

## Requirements

- `raven-python>=5.4.0`
- `python>=3.3`
- `aiohttp>=0.19`

## Usage

After installing the package, configure the client with the transport:

```
import asyncio

from raven import Client
from raven_aiohttp import AioHttpTransport

client = Client(transport=AioHttpTransport)

try:
    1 / 0
except ZeroDivisionError:
    client.captureException()

# There is built-in graceful shutdown

loop = asyncio.get_event_loop()
loop.run_until_complete(client.remote.get_transport().close(timeout=2))
```
