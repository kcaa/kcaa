#!/usr/bin/env python

import multiprocessing
import signal
import sys

import kcaa


def main(argv):
    args = kcaa.flags.parse_args(argv[1:])

    logger = kcaa.logenv.setup_logger()
    logger.debug('Logger setup finished.')

    to_exit = multiprocessing.Event()
    p = multiprocessing.Process(target=kcaa.controller.control,
                                args=(args, to_exit))
    p.start()
    logger.debug('Controller process started.')

    def handle_sigint(signal, frame):
        logger.info('SIGINT received in the main process. Exiting...')
        to_exit.set()
        p.join()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    p.join()
    logger.info('Shutting down the main process.')


if __name__ == '__main__':
    main(sys.argv)
