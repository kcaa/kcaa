#!/usr/bin/env python

import datetime
import logging
import multiprocessing
import signal
import sys

import kcaa


class ShortLogFormatter(logging.Formatter):

    def format(self, record):
        now = datetime.datetime.now()
        return '{} {:5s}: {}'.format(now.strftime('%H:%M:%S'),
                                     record.levelname[:5],
                                     record.getMessage())


def main(argv):
    args = kcaa.flags.parse_args(argv[1:])

    # Log to stdout.
    logger = logging.getLogger('kcaa')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(ShortLogFormatter())
    logger.addHandler(handler)

    to_exit = multiprocessing.Event()
    p = multiprocessing.Process(target=kcaa.controller.control,
                                args=(args, to_exit))
    p.start()

    def handle_sigint(signal, frame):
        logger.info('SIGINT received in the main process. Exiting...')
        to_exit.set()
        p.join()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    p.join()


if __name__ == '__main__':
    main(sys.argv)
