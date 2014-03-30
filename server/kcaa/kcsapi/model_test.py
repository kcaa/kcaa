#!/usr/bin/env python

import pytest

import model


def main():
    import doctest
    doctest.testmod(model)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
