#!/usr/bin/env python

import pytest

import ship


SPF = ship.ShipPropertyFilter


class TestShipPropertyFilter(object):

    def test_apply_id_equal_match(self):
        s = ship.Ship(id=123)
        spf = SPF(property=u'id', value=123, operator=SPF.OPERATOR_EQUAL)
        assert spf.apply(s)

    def test_apply_id_equal_no_match(self):
        s = ship.Ship(id=123)
        spf = SPF(property=u'id', value=124, operator=SPF.OPERATOR_EQUAL)
        assert not spf.apply(s)

    def test_apply_non_existing_property(self):
        s = ship.Ship(id=123)
        spf = SPF(property=u'id_non_existing', value=124,
                  operator=SPF.OPERATOR_EQUAL)
        assert not spf.apply(s)

    def test_apply_non_existing_operator(self):
        s = ship.Ship(id=123)
        spf = SPF(property=u'id', value=123, operator=-1)
        assert not spf.apply(s)

    def test_apply_name(self):
        s = ship.Ship(name=u'foo')
        spf = SPF(property=u'name', value=u'foo', operator=SPF.OPERATOR_EQUAL)
        assert spf.apply(s)


def main():
    import doctest
    doctest.testmod(ship)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
