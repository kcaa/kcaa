#!/usr/bin/env python

import logging
import multiprocessing
import sys

import controller
import flags
import server


def main(argv):
    args = flags.parse_args(argv[1:])

    # Log to stdout.
    logger = logging.getLogger('kcaa')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    to_exit = multiprocessing.Event()
    controller_conn, server_conn = multiprocessing.Pipe()
    pc = multiprocessing.Process(target=controller.control,
                                 args=(args, server_conn, to_exit))
    ps = multiprocessing.Process(target=server.handle_server,
                                 args=(args, controller_conn, to_exit))
    pc.start()
    ps.start()
    pc.join()
    ps.join()


if __name__ == '__main__':
    main(sys.argv)
