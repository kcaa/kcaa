#!/usr/bin/env python

import pytest

import mission


class TestMissionList(object):

    def pytest_funcarg__mission_list(self):
        mission_list = mission.MissionList()
        mission_list.missions.extend([
            mission.Mission(
                id=1,
                name=u'Mission1',
                maparea=mission.Mission.MAPAREA_BASE),
            mission.Mission(
                id=2,
                name=u'Mission2',
                maparea=mission.Mission.MAPAREA_BASE),
            mission.Mission(
                id=3,
                name=u'Mission3',
                maparea=mission.Mission.MAPAREA_SOUTHWESTERN_ISLANDS),
            mission.Mission(
                id=4,
                name=u'Mission4',
                maparea=mission.Mission.MAPAREA_SOUTHWESTERN_ISLANDS),
            mission.Mission(
                id=5,
                name=u'Mission5',
                maparea=mission.Mission.MAPAREA_SOUTHWESTERN_ISLANDS)])
        return mission_list

    def test_get_mission(self, mission_list):
        assert mission_list.get_mission(0) is None
        assert mission_list.get_mission(1) == mission_list.missions[0]
        assert mission_list.get_mission(2) == mission_list.missions[1]
        assert mission_list.get_mission(3) == mission_list.missions[2]
        assert mission_list.get_mission(4) == mission_list.missions[3]
        assert mission_list.get_mission(5) == mission_list.missions[4]
        assert mission_list.get_mission(6) is None

    def test_get_index_in_mapaea(self, mission_list):
        assert mission_list.get_index_in_maparea(mission_list.missions[0]) == 0
        assert mission_list.get_index_in_maparea(mission_list.missions[1]) == 1
        assert mission_list.get_index_in_maparea(mission_list.missions[2]) == 0
        assert mission_list.get_index_in_maparea(mission_list.missions[3]) == 1
        assert mission_list.get_index_in_maparea(mission_list.missions[4]) == 2


def main():
    import doctest
    doctest.testmod(mission)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
