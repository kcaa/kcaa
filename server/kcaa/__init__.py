#!/usr/bin/env python

import browser
import controller
import event
import flags
import kcsapi
import kcsapi_util
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
    doctest.testmod(proxy_util)
    doctest.testmod(server)
    doctest.testmod(task)
    import os.path
    import pytest
    pytest.main(args=[os.path.dirname(__file__)])


if __name__ == '__main__':
    main()
