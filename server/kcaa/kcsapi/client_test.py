#!/usr/bin/env python

import pytest

import client
from kcaa import screens


class TestScreen(object):

    def update(self, screen, api_name):
        screen.update(api_name, None, None, None, False)

    def update_sequence(self, screen, api_names):
        for api_name in api_names:
            screen.update(api_name, None, None, None, False)

    def test_mission_result(self):
        screen = client.Screen()
        assert screen.screen == screens.UNKNOWN
        self.update(screen, '/api_get_member/deck_port')
        assert screen.screen == screens.PORT_MAIN
        self.update(screen, '/api_req_mission/result')
        assert screen.screen == screens.MISSION_RESULT
        self.update(screen, '/api_get_member/deck_port')
        assert screen.screen == screens.MISSION_RESULT

    def test_mission_result_real_sequence(self):
        screen = client.Screen()
        screen.screen = screens.PORT
        self.update_sequence(screen, [
            '/api_auth_member/logincheck',
            '/api_get_member/material',
            '/api_get_member/deck_port',
            '/api_get_member/ndock',
            '/api_get_member/ship3',
            '/api_get_member/basic',
            '/api_req_mission/result',
            '/api_get_member/deck_port',
            '/api_get_member/basic',
            '/api_get_member/ship2',
            '/api_get_member/material',
            '/api_get_member/useitem',
        ])
        assert screen.screen == screens.MISSION_RESULT


def main():
    import doctest
    doctest.testmod(client)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
