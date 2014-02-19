#!/usr/bin/env python

import multiprocessing
import sys

import kcaa


def main(argv):
    args = kcaa.flags.parse_args(argv[1:])
    p = multiprocessing.Process(target=kcaa.controller.control, args=(args,))
    p.start()
    p.join()


if __name__ == '__main__':
    main(sys.argv)
