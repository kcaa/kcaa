#!/usr/bin/env python

import pytest

import jsonobject
import ship


SPF = ship.ShipPropertyFilter
SP = ship.ShipPredicate


class TestShipList(object):

    def pytest_funcarg__ship_list(self):
        ship_list = ship.ShipList()
        ship_list.ships['1'] = ship.Ship(
            id=1,
            name=u'Ship 1',
            upgrade_to=1002)
        return ship_list

    def pytest_funcarg__ship_defs(self):
        ship_defs = ship.ShipDefinitionList()
        ship_defs.ships['1001'] = ship.ShipDefinition(
            id=1001,
            name=u'Ship 1001',
            ship_type=ship.ShipDefinition.SHIP_TYPE_DESTROYER,
            armor=ship.Variable(baseline=1, maximum=2),
            avoidance=ship.Variable(baseline=3, maximum=4),
            firepower=ship.Variable(baseline=5, maximum=6),
            thunderstroke=ship.Variable(baseline=7, maximum=8),
            anti_air=ship.Variable(baseline=9, maximum=10),
            anti_submarine=ship.Variable(baseline=11, maximum=12),
            scouting=ship.Variable(baseline=13, maximum=14),
            luck=ship.Variable(baseline=15, maximum=16),
            upgrade_to=1002)
        ship_defs.ships['1002'] = ship.ShipDefinition(
            id=1001,
            name=u'Ship 1002',
            armor=ship.Variable(baseline=11, maximum=12),
            avoidance=ship.Variable(baseline=13, maximum=14),
            firepower=ship.Variable(baseline=15, maximum=16),
            thunderstroke=ship.Variable(baseline=17, maximum=18),
            anti_air=ship.Variable(baseline=19, maximum=110),
            anti_submarine=ship.Variable(baseline=111, maximum=112),
            scouting=ship.Variable(baseline=113, maximum=114),
            luck=ship.Variable(baseline=115, maximum=116),
            upgrade_to=1002)
        return ship_defs

    def pytest_funcarg__ship_data(self):
        return jsonobject.parse_text("""{
            "api_id": 1,
            "api_ship_id": 1001,
            "api_lv": 2,
            "api_nowhp": 3,
            "api_maxhp": 4,
            "api_cond": 5,
            "api_fuel": 6,
            "api_bull": 7,
            "api_soukou": [8, 9],
            "api_kaihi": [10, 11],
            "api_karyoku": [12, 13],
            "api_raisou": [14, 15],
            "api_taiku": [16, 17],
            "api_taisen": [18, 19],
            "api_sakuteki": [20, 21],
            "api_lucky": [22, 23],
            "api_kyouka": [1, 2, 3, 4, 0],
            "api_sortno": 1001,
            "api_backs": 1,
            "api_exp": [24, 25, 26],
            "api_locked": 1
        }""")

    # TODO: Test /api_port/port.

    def test_update_ship2(self, ship_defs, ship_data):
        response = jsonobject.parse({'api_data': [ship_data]})
        ship_list = ship.ShipList()
        ship_list.update('/api_get_member/ship2', None, response,
                         {'ShipDefinitionList': ship_defs}, False)
        assert '1' in ship_list.ships
        ship_ = ship_list.ships['1']
        assert ship_.id == 1
        assert ship_.name == u'Ship 1001'
        assert ship_.upgrade_to == 1002


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
        assert SPF.get_property_value(ship.Ship(id=124), ['id']) == 124

    def test_get_property_nested_hitpoint(self):
        s = ship.Ship(hitpoint=ship.Variable(current=52, maximum=53))
        assert SPF.get_property_value(s, ['hitpoint', 'current']) == 52
        assert SPF.get_property_value(s, ['hitpoint', 'maximum']) == 53


class TestShipPredicate(object):

    def test_apply_empty(self):
        # An empty predicate is always considered true.
        sp = SP()
        assert sp.apply(ship.Ship(id=123))

    def test_apply_property_filter_id_equal(self):
        sp = SP(property_filter=SPF(
            property=u'id', value=123, operator=SPF.OPERATOR_EQUAL))
        assert sp.apply(ship.Ship(id=123))
        assert not sp.apply(ship.Ship(id=124))

    def test_apply_not_property_filter_id_equal(self):
        sp = SP(not_=SP(property_filter=SPF(
            property=u'id', value=123, operator=SPF.OPERATOR_EQUAL)))
        assert not sp.apply(ship.Ship(id=123))
        assert sp.apply(ship.Ship(id=124))

    def test_apply_or_property_filter_ship_types(self):
        sp = SP(or_=[
            SP(property_filter=SPF(
                property=u'ship_type', value=2, operator=SPF.OPERATOR_EQUAL)),
            SP(property_filter=SPF(
                property=u'ship_type', value=3, operator=SPF.OPERATOR_EQUAL)),
            SP(property_filter=SPF(
                property=u'ship_type', value=4, operator=SPF.OPERATOR_EQUAL))])
        assert not sp.apply(ship.Ship(ship_type=1))
        assert sp.apply(ship.Ship(ship_type=2))
        assert sp.apply(ship.Ship(ship_type=3))
        assert sp.apply(ship.Ship(ship_type=4))
        assert not sp.apply(ship.Ship(ship_type=5))

    def test_apply_and_property_filter_ship_type_and_level(self):
        sp = SP(and_=[
            SP(property_filter=SPF(
                property=u'ship_type', value=13, operator=SPF.OPERATOR_EQUAL)),
            SP(property_filter=SPF(
                property=u'level', value=10,
                operator=SPF.OPERATOR_GREATER_THAN_EQUAL))])
        assert not sp.apply(ship.Ship(ship_type=12, level=9))
        assert not sp.apply(ship.Ship(ship_type=12, level=10))
        assert not sp.apply(ship.Ship(ship_type=12, level=11))
        assert not sp.apply(ship.Ship(ship_type=13, level=9))
        assert sp.apply(ship.Ship(ship_type=13, level=10))
        assert sp.apply(ship.Ship(ship_type=13, level=11))

    def test_apply_not_submarines_or_enough_thunderstroke_and_armor(self):
        # This is a test for an example realistic predicate, written in JSON.
        sp = SP.parse_text("""{
            "or": [
                {
                    "not": {
                        "or": [
                            {
                                "property_filter": {
                                    "property": "ship_type",
                                    "value": 13,
                                    "operator": 0
                                }
                            },
                            {
                                "property_filter": {
                                    "property": "ship_type",
                                    "value": 14,
                                    "operator": 0
                                }
                            },
                            {
                                "property_filter": {
                                    "property": "ship_type",
                                    "value": 20,
                                    "operator": 0
                                }
                            }
                        ]
                    }
                },
                {
                    "and": [
                        {
                            "property_filter": {
                                "property": "thunderstroke.current",
                                "value": 70,
                                "operator": 5
                            }
                        },
                        {
                            "property_filter": {
                                "property": "armor.current",
                                "value": 15,
                                "operator": 5
                            }
                        }
                    ]
                }
            ]
        }""")
        # Not submarine, OK to pass.
        assert sp.apply(ship.Ship(
            ship_type=2,
            thunderstroke=ship.Variable(current=10),
            armor=ship.Variable(current=10)))
        # These are submarines and not enough parameters. NG to pass.
        assert not sp.apply(ship.Ship(
            ship_type=13,
            thunderstroke=ship.Variable(current=10),
            armor=ship.Variable(current=10)))
        assert not sp.apply(ship.Ship(
            ship_type=14,
            thunderstroke=ship.Variable(current=10),
            armor=ship.Variable(current=10)))
        assert not sp.apply(ship.Ship(
            ship_type=20,
            thunderstroke=ship.Variable(current=10),
            armor=ship.Variable(current=10)))
        # Submarine but enough parameters. OK to pass.
        assert sp.apply(ship.Ship(
            ship_type=13,
            thunderstroke=ship.Variable(current=70),
            armor=ship.Variable(current=15)))


def main():
    import doctest
    doctest.testmod(ship)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
