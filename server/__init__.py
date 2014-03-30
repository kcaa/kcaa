#!/usr/bin/env python

import kcaa
import server_main


def main():
    import doctest
    doctest.testmod(kcaa)
    doctest.testmod(server_main)
    import pytest
    import sys
    sys.exit(pytest.main())


if __name__ == '__main__':
    main()
