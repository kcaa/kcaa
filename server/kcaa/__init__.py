#!/usr/bin/env python

import browser
import controller
import event
import flags
import kcsapi
import kcsapi_util
import manipulator_util
import manipulators
import proxy_util
import server
import task


def main():
    import doctest
    doctest.testmod(browser)
    doctest.testmod(controller)
    doctest.testmod(event)
    doctest.testmod(flags)
    doctest.testmod(kcsapi)
    doctest.testmod(kcsapi_util)
    doctest.testmod(manipulator_util)
    doctest.testmod(manipulators)
    doctest.testmod(proxy_util)
    doctest.testmod(server)
    doctest.testmod(task)
    import pytest
    import sys
    sys.exit(pytest.main())


if __name__ == '__main__':
    main()
