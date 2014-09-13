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
def setup_logger(debug, log_file, log_level):
    global _logger
    if _logger:
        return _logger
    logger = logging.getLogger('kcaa')
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG if debug else logging.INFO)
    formatter = ShortLogFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # Set up file logger.
    if log_file:
        handler = logging.FileHandler(log_file, mode='w')
        log_level_num = getattr(logging, log_level, None)
        if not isinstance(log_level_num, int):
            raise ValueError(
                'Log level {} is invalid. Valid values include DEBUG, INFO, '
                'WARNING, or ERROR.'.format(log_level))
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    _logger = logger
    return logger
