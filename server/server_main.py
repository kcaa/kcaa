#!/usr/bin/env python

import multiprocessing
import sys

import browser
import flags
import server


def main(argv):
    args = flags.parse_args(argv[1:])
    to_exit = multiprocessing.Event()
    browser_conn, server_conn = multiprocessing.Pipe()
    ps = multiprocessing.Process(target=server.handle_server,
                                 args=(args, browser_conn, to_exit))
    pb = multiprocessing.Process(target=browser.monitor_browser,
                                 args=(args, server_conn, to_exit))
    ps.start()
    pb.start()
    ps.join()
    pb.join()


if __name__ == '__main__':
    main(sys.argv)
