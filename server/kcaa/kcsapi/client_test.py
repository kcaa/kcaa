#!/usr/bin/env python

import pytest

import client


class TestScreen(object):

    def test_foo(self):
        pass


def main():
    import doctest
    doctest.testmod(client)
    pytest.main(args=[__file__.replace('.pyc', '.py')])


if __name__ == '__main__':
    main()
