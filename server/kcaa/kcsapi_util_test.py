#!/usr/bin/env python

import pytest

import kcsapi
import kcsapi_util


class TestKCSAPIHandler(object):

    def pytest_funcarg__handler(self):
        return kcsapi_util.KCSAPIHandler(
            None, kcsapi.prefs.Preferences(), False)

    def test_get_kcsapi_responses_ignore_unrelated_request(self, handler):
        entries = [
            {
                'request': {
                    'url': 'http://www.example.com/unrelated/url',
                },
            },
        ]
        assert list(handler.get_kcsapi_responses(entries)) == []

    def test_get_kcsapi_responses_parsed_as_jsonobject(self, handler):
        entries = [
            {
                'request': {
                    'url': 'http://www.example.com/kcsapi/api_example',
                    'postData': {
                        'params': [
                            {
                                'name': 'api_verno',
                                'value': '1',
                            },
                            {
                                'name': 'api_token',
                                'value': '0123456789abcdef',
                            },
                        ],
                    },
                },
                'response': {
                    'content': {
                        'text': 'svdata={"foo": "bar"}',
                    },
                },
            },
        ]
        responses = list(handler.get_kcsapi_responses(entries))
        assert len(responses) == 1
        api_name, request, response = responses[0]
        assert api_name == '/api_example'
        assert request.api_verno == '1'
        assert request.api_token == '0123456789abcdef'
        assert response.foo == 'bar'


def main():
    import doctest
    doctest.testmod(kcsapi_util)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
