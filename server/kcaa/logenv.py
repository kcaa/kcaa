#!/usr/bin/env python

import datetime
import logging
import sys


_logger = None


class ShortLogFormatter(logging.Formatter):

    def format(self, record):
        now = datetime.datetime.now()
        return '{} {:5s}: {}'.format(now.strftime('%H:%M:%S'),
                                     record.levelname[:5],
                                     record.getMessage())


# Set up a logger.
# On Linux it seems it's enough to call this from the main process. Windows
# seems not comfortable with that -- needs to be called from each subprocess.
def setup_logger():
    global _logger
    if _logger:
        return _logger
    logger = logging.getLogger('kcaa')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(ShortLogFormatter())
    logger.addHandler(handler)
    _logger = logger
    return logger
