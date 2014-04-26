#!/usr/bin/env python

import pytest

import kcsapi_util


class TestKCSAPIHandler(object):

    def pytest_funcarg__kcsapi_handler(self):
        return kcsapi_util.KCSAPIHandler(None, False)

    def test_get_kcsapi_responses_ignore_unrelated_request(
            self, kcsapi_handler):
        entries = [
            {
                'request': {
                    'url': 'http://www.example.com/unrelated/url',
                }
            },
        ]
        assert list(kcsapi_handler.get_kcsapi_responses(entries)) == []


def main():
    import doctest
    doctest.testmod(kcsapi_util)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
