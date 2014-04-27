#!/usr/bin/env python

import datetime
import logging
import sys

import browser
import controller
import event
import flags
import kcsapi
import kcsapi_util
import manipulator_util
import manipulators
import proxy_util
import server
import task


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
    logger = logging.getLogger('kcaa')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(ShortLogFormatter())
    logger.addHandler(handler)
    return logger


def main():
    import doctest
    doctest.testmod(browser)
    doctest.testmod(controller)
    doctest.testmod(event)
    doctest.testmod(flags)
    doctest.testmod(kcsapi)
    doctest.testmod(kcsapi_util)
    doctest.testmod(manipulator_util)
    doctest.testmod(manipulators)
    doctest.testmod(proxy_util)
    doctest.testmod(server)
    doctest.testmod(task)
    import pytest
    import sys
    sys.exit(pytest.main())


if __name__ == '__main__':
    main()
