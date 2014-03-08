#!/usr/bin/env python

import pytest

import client
from kcaa import screens


class TestScreen(object):

    def test_mission_result(self):
        screen = client.Screen()
        assert screen.screen == screens.UNKNOWN
        screen.update('/api_get_member/deck_port', None, None, None, False)
        assert screen.screen == screens.PORT
        screen.update('/api_req_mission/result', None, None, None, False)
        assert screen.screen == screens.MISSION_RESULT
        screen.update('/api_get_member/deck_port', None, None, None, False)
        assert screen.screen == screens.MISSION_RESULT


def main():
    import doctest
    doctest.testmod(client)
    pytest.main(args=[__file__.replace('.pyc', '.py')])


if __name__ == '__main__':
    main()
