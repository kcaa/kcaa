#!/usr/bin/env python

import pytest

import fleet
import jsonobject


class TestFleetList(object):

    def pytest_funcarg__fleet_list(self):
        fleet_list = fleet.FleetList()
        # Why?
        fleet_list.fleets = []
        fleet_list.fleets.append(fleet.Fleet(
            id=1,
            name=u'FleetName',
            ship_ids=[1, 2, 3]))
        return fleet_list

    def test_update(self):
        response = jsonobject.parse_text("""
            {
                "api_data": {
                    "api_deck_port": [
                        {
                            "api_id": 1,
                            "api_name": "FleetName",
                            "api_ship": [
                                123,
                                456,
                                789,
                                -1,
                                -1,
                                -1
                            ],
                            "api_mission": [
                                1,
                                111,
                                0,
                                0
                            ]
                        }
                    ]
                }
            }
        """)
        fleet_list = fleet.FleetList()
        fleet_list.update('/api_port/port', None, response, None, False)
        assert len(fleet_list.fleets) == 1
        fleet_ = fleet_list.fleets[0]
        assert fleet_.id == 1
        assert fleet_.name == 'FleetName'
        assert fleet_.ship_ids == [123, 456, 789]
        assert fleet_.mission_id == 111
        assert not fleet_.mission_complete

    def test_update_ship_deployment(self, fleet_list):
        request = jsonobject.parse_text("""
            {
                "api_id": "1",
                "api_ship_idx": "3",
                "api_ship_id": "4"
            }
        """)
        fleet_list.update(
            '/api_req_hensei/change', request, None, None, False)
        assert fleet_list.fleets[0].ship_ids == [1, 2, 3, 4]

    def test_update_ship_removal(self, fleet_list):
        request = jsonobject.parse_text("""
            {
                "api_id": "1",
                "api_ship_idx": "1",
                "api_ship_id": "-1"
            }
        """)
        fleet_list.update(
            '/api_req_hensei/change', request, None, None, False)
        assert fleet_list.fleets[0].ship_ids == [1, 3]


def main():
    import doctest
    doctest.testmod(fleet)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
