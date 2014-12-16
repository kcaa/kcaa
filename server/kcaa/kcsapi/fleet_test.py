#!/usr/bin/env python

import pytest

import fleet
import jsonobject


class TestFleetList(object):

    def pytest_funcarg__fleet_list(self):
        fleet_list = fleet.FleetList()
        fleet_list.fleets.append(fleet.Fleet(
            id=1,
            name=u'FleetName',
            ship_ids=[1, 2, 3]))
        return fleet_list

    def pytest_funcarg__fleet_list_2(self):
        fleet_list = fleet.FleetList()
        fleet_list.fleets.append(fleet.Fleet(
            id=1,
            name=u'FleetName1',
            ship_ids=[1, 2, 3]))
        fleet_list.fleets.append(fleet.Fleet(
            id=2,
            name=u'FleetName2',
            ship_ids=[4, 5, 6, 7]))
        return fleet_list

    def test_update(self):
        response = jsonobject.parse_text("""{
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
        }""")
        fleet_list = fleet.FleetList()
        fleet_list.update('/api_port/port', None, response, {}, False)
        assert len(fleet_list.fleets) == 1
        fleet_ = fleet_list.fleets[0]
        assert fleet_.id == 1
        assert fleet_.name == u'FleetName'
        assert fleet_.ship_ids == [123, 456, 789]
        assert fleet_.mission_id == 111
        assert not fleet_.mission_complete

    def test_update_ship_deployment(self, fleet_list):
        # Add the ship 4 to the end of the ship list.
        request = jsonobject.parse_text("""{
            "api_id": "1",
            "api_ship_idx": "3",
            "api_ship_id": "4"
        }""")
        fleet_list.update(
            '/api_req_hensei/change', request, None, {}, False)
        assert fleet_list.fleets[0].ship_ids == [1, 2, 3, 4]

    def test_update_ship_removal(self, fleet_list):
        # Remove the ship at the index 1 (the second ship).
        request = jsonobject.parse_text("""{
            "api_id": "1",
            "api_ship_idx": "1",
            "api_ship_id": "-1"
        }""")
        fleet_list.update(
            '/api_req_hensei/change', request, None, {}, False)
        assert fleet_list.fleets[0].ship_ids == [1, 3]

    def test_update_fleet_clearance(self, fleet_list):
        # Remove all the ships except the flag ship.
        request = jsonobject.parse_text("""{
            "api_id": "1",
            "api_ship_idx": "0",
            "api_ship_id": "-2"
        }""")
        fleet_list.update(
            '/api_req_hensei/change', request, None, {}, False)
        assert fleet_list.fleets[0].ship_ids == [1]

    def test_update_ship_swapping(self, fleet_list):
        # Swap the ship at the index 1 with the ship 3.
        request = jsonobject.parse_text("""{
            "api_id": "1",
            "api_ship_idx": "1",
            "api_ship_id": "3"
        }""")
        fleet_list.update(
            '/api_req_hensei/change', request, None, {}, False)
        assert fleet_list.fleets[0].ship_ids == [1, 3, 2]

    def test_update_ship_swapping_between_fleets(self, fleet_list_2):
        # Swap the ship at the index 1 with the ship 5.
        # Note that the ship 5 is in the second fleet.
        request = jsonobject.parse_text("""{
            "api_id": "1",
            "api_ship_idx": "1",
            "api_ship_id": "5"
        }""")
        fleet_list_2.update(
            '/api_req_hensei/change', request, None, {}, False)
        assert fleet_list_2.fleets[0].ship_ids == [1, 5, 3]
        assert fleet_list_2.fleets[1].ship_ids == [4, 2, 6, 7]


def main():
    import doctest
    doctest.testmod(fleet)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
