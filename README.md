# raven-aiohttp

A transport for [raven-python](https://github.com/getsentry/raven-python) which supports Python 3's asyncio interface.

## Requirements

- `raven-python>=5.4.0`
- `python>=3.3`
- `aiohttp>=0.19`

## Usage

See `example.py` for an example that you can run like this:
```bash
$ python3 example.py
```

For testing, you can set your DSN like this:
```bash
$ SENTRY_DSN=https://public:secret@example.com/1 python3 example.py
```
