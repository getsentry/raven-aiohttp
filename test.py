import asyncio
import logging
from functools import partial

from raven import Client
from raven_aiohttp import AioHttpTransport


logging.basicConfig(level=logging.DEBUG)

client = Client(
    'https://daa02df1c75044ff8b6e2d150dd597c7:67c55fe82258442caa3b02a68aace22b@sentry.io/217727',
    transport=partial(AioHttpTransport, background_workers=1,queue_maxsize=1),
)

try:
    1 / 0
except ZeroDivisionError:
    client.captureException()


loop = asyncio.get_event_loop()
# loop.run_until_complete(asyncio.sleep(2))
loop.run_until_complete(client.remote.get_transport().close())
