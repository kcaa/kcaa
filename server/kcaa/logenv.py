#!/usr/bin/env python

import datetime
import logging
import sys


_logger = None


class ShortLogFormatter(logging.Formatter):

    def format(self, record):
        now = datetime.datetime.now()
        message = record.getMessage()
        if isinstance(message, str):
            message = message.decode('utf8')
        return u'{} {:5s}: {}'.format(now.strftime('%H:%M:%S'),
                                      record.levelname[:5],
                                      message)


# Set up a logger.
# On Linux it seems it's enough to call this from the main process. Windows
# seems not comfortable with that -- needs to be called from each subprocess.
def setup_logger(debug, log_file, log_level):
    global _logger
    if _logger:
        return _logger
    logger = logging.getLogger('kcaa')
    logger.setLevel(logging.DEBUG)
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


# Set up a logger for test.
# Call this from a specific test case you want to see messages, or call at the
# top level of the test file. Otherwise logging messages are not caught at all.
def setup_logger_for_test():
    logger = logging.getLogger('kcaa')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(ShortLogFormatter())
    logger.addHandler(handler)
    return logger
