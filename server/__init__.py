#!/usr/bin/env python

import kcaa
import server_main


def main():
    import doctest
    doctest.testmod(kcaa)
    doctest.testmod(server_main)
    import os.path
    import pytest
    pytest.main(args=[os.path.dirname(__file__)])


if __name__ == '__main__':
    main()
