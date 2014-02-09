#!/usr/bin/env python

import sys

import browser
import flags


def main(argv):
    args = flags.parse_args(argv[1:])
    browser.setup(args)


if __name__ == '__main__':
    main(sys.argv)
