#!/usr/bin/env python

import pytest

import manipulator_util


class TestManipulatorManager(object):

    def pytest_funcarg__manager(self, request):
        return manipulator_util.ManipulatorManager(None, {}, 0)

    def test_in_schedule_fragment(self):
        in_schedule_fragment = (
            manipulator_util.ManipulatorManager.in_schedule_fragment)
        assert in_schedule_fragment(0, [0, 3600])
        assert in_schedule_fragment(1800, [0, 3600])
        assert in_schedule_fragment(3599, [0, 3600])
        assert not in_schedule_fragment(3600, [0, 3600])
        assert not in_schedule_fragment(5400, [0, 3600])


def main():
    import doctest
    doctest.testmod(manipulator_util)
    pytest.main(args=[__file__.replace('.pyc', '.py')])


if __name__ == '__main__':
    main()
