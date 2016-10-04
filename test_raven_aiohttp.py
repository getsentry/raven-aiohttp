from raven import Client
from raven_aiohttp import AIOHTTPTransport


def test_simple():
    client = Client('http://public:secret@example.com/1',
                    transport=AIOHTTPTransport)
    assert client.is_enabled()
    # TODO(dcrmer): figure out how to actually test this
    # assert client.captureMessage('test')
