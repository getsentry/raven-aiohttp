#!/usr/bin/env python3

import asyncio
from raven import Client
from raven_aiohttp import AioHttpTransport


async def function_with_error():

    try:
        1 / 0
    except:
        client = Client(transport=AioHttpTransport)
        print(client.captureException())

        # HACK to be sure the event loop doesn't terminate before completing:
        # https://github.com/getsentry/raven-aiohttp/issues/15
        await asyncio.sleep(2)


if __name__ == '__main__':

    loop = asyncio.get_event_loop()
    loop.run_until_complete(function_with_error())
    # important because it will tell you if your (sentry) task has not yet run:
    loop.close()
