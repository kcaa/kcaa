#!/usr/bin/env python

import multiprocessing
import sys

import controller
import flags
import server


def main(argv):
    args = flags.parse_args(argv[1:])
    to_exit = multiprocessing.Event()
    controller_conn, server_conn = multiprocessing.Pipe()
    pc = multiprocessing.Process(target=controller.controll,
                                 args=(args, server_conn, to_exit))
    ps = multiprocessing.Process(target=server.handle_server,
                                 args=(args, controller_conn, to_exit))
    pc.start()
    ps.start()
    pc.join()
    ps.join()


if __name__ == '__main__':
    main(sys.argv)
