import logging


class TestHandler(logging.Handler):

    def __init__(self, records, msgs, *args, **kwargs):
        self.records = records
        self.msgs = msgs
        super().__init__(*args, **kwargs)

    def emit(self, record):
        self.records.append(record)

        self.msgs.append(self.format(record))


class Logger:

    def __init__(self, name, level=logging.NOTSET):
        self.name = name
        self.level = level

        self.records, self.msgs = [], []

        self.logger = logging.getLogger(self.name)
        self.handler = TestHandler(self.records, self.msgs, level=self.level)

    def __enter__(self):
        self.logger.addHandler(self.handler)

        return self

    def __exit__(self, *exc_info):
        self.logger.removeHandler(self.handler)
