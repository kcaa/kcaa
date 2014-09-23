#!/usr/bin/env python

import pytest

import ship


SPF = ship.ShipPropertyFilter


class TestShipPropertyFilter(object):

    def test_apply_id_equal_match(self):
        spf = SPF(property=u'id', value=123, operator=SPF.OPERATOR_EQUAL)
        assert spf.apply(ship.Ship(id=123))

    def test_apply_id_equal_no_match(self):
        spf = SPF(property=u'id', value=124, operator=SPF.OPERATOR_EQUAL)
        assert not spf.apply(ship.Ship(id=123))

    def test_apply_id_equal_none(self):
        # We consider that the filter condition checking if a value is None
        # (null) always return False. Such a filter is tricky.
        spf = SPF(property=u'id', value=None, operator=SPF.OPERATOR_EQUAL)
        assert not spf.apply(ship.Ship(id=None))

    def test_apply_non_existing_property(self):
        spf = SPF(property=u'id_non_existing', value=124,
                  operator=SPF.OPERATOR_EQUAL)
        assert not spf.apply(ship.Ship(id=123))

    def test_apply_non_existing_operator(self):
        spf = SPF(property=u'id', value=123, operator=-1)
        assert not spf.apply(ship.Ship(id=123))

    def test_apply_name_equal(self):
        spf = SPF(property=u'name', value=u'foo', operator=SPF.OPERATOR_EQUAL)
        assert spf.apply(ship.Ship(name=u'foo'))

    def test_apply_level_not_equal(self):
        spf = SPF(property=u'level', value=77, operator=SPF.OPERATOR_NOT_EQUAL)
        assert spf.apply(ship.Ship(level=76))
        assert not spf.apply(ship.Ship(level=77))
        assert spf.apply(ship.Ship(level=78))

    def test_apply_level_less_than(self):
        spf = SPF(property=u'level', value=77, operator=SPF.OPERATOR_LESS_THAN)
        assert spf.apply(ship.Ship(level=76))
        assert not spf.apply(ship.Ship(level=77))
        assert not spf.apply(ship.Ship(level=78))

    def test_apply_level_less_than_equal(self):
        spf = SPF(property=u'level', value=77,
                  operator=SPF.OPERATOR_LESS_THAN_EQUAL)
        assert spf.apply(ship.Ship(level=76))
        assert spf.apply(ship.Ship(level=77))
        assert not spf.apply(ship.Ship(level=78))

    def test_apply_level_greater_than(self):
        spf = SPF(property=u'level', value=77,
                  operator=SPF.OPERATOR_GREATER_THAN)
        assert not spf.apply(ship.Ship(level=76))
        assert not spf.apply(ship.Ship(level=77))
        assert spf.apply(ship.Ship(level=78))

    def test_apply_level_greater_than_equal(self):
        spf = SPF(property=u'level', value=77,
                  operator=SPF.OPERATOR_GREATER_THAN_EQUAL)
        assert not spf.apply(ship.Ship(level=76))
        assert spf.apply(ship.Ship(level=77))
        assert spf.apply(ship.Ship(level=78))

    def test_apply_hitpoint_current_equal(self):
        spf = SPF(property=u'hitpoint.current', value=52,
                  operator=SPF.OPERATOR_EQUAL)
        assert spf.apply(ship.Ship(hitpoint=ship.Variable(current=52)))

    def test_get_property_value_id(self):
        assert SPF.get_property_value(ship.Ship(id=123), ['id']) == 123


def main():
    import doctest
    doctest.testmod(ship)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
