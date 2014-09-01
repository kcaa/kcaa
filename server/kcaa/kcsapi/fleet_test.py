#!/usr/bin/env python

import pytest

import fleet
import jsonobject


class TestFleetList(object):

    def test_update(self):
        fleet_list = fleet.FleetList()
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
        fleet_list.update('/api_port/port', None, response, None, False)
        assert len(fleet_list.fleets)
        fleet_ = fleet_list.fleets[0]
        assert fleet_.id == 1
        assert fleet_.name == 'FleetName'
        assert fleet_.ship_ids == [123, 456, 789]
        assert fleet_.mission_id == 111
        assert not fleet_.mission_complete


def main():
    import doctest
    doctest.testmod(fleet)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
