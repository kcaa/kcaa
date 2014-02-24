#!/usr/bin/env python

import jsonobject
import model
import resource


class Mission(jsonobject.JSONSerializableObject):

    id = jsonobject.ReadonlyJSONProperty('id', value_type=int)
    """ID."""
    name = jsonobject.ReadonlyJSONProperty('name', value_type=unicode)
    """Name."""
    description = jsonobject.ReadonlyJSONProperty('description',
                                                  value_type=unicode)
    """Description."""
    difficulty = jsonobject.ReadonlyJSONProperty('difficulty', value_type=int)
    """Difficulty."""
    DIFFICULTY_E = 1
    DIFFICULTY_D = 2
    DIFFICULTY_C = 3
    DIFFICULTY_B = 4
    DIFFICULTY_A = 5
    DIFFICULTY_S = 6
    DIFFICULTY_SS = 7
    DIFFICULTY_SSS = 8
    maparea = jsonobject.ReadonlyJSONProperty('maparea', value_type=int)
    """Map area."""
    MAPAREA_BASE = 1
    MAPAREA_SOUTHWESTERN_ISLANDS = 2
    MAPAREA_NORTH = 3
    MAPAREA_WEST = 4
    MAPAREA_SOUTH = 5
    state = jsonobject.ReadonlyJSONProperty('state', value_type=int)
    """State."""
    STATE_NEW = 0
    STATE_ACTIVE = 1
    STATE_COMPLETE = 2
    time = jsonobject.ReadonlyJSONProperty('time', value_type=int)
    """Required time to complete in minutes."""
    consumption = jsonobject.ReadonlyJSONProperty(
        'consumption', value_type=resource.ResourcePercentage)
    """Resource consumption percentage relative to the fleet capacity."""
    bonus_items = jsonobject.ReadonlyJSONProperty('bonus_items')
    """TODO: Bonus items?"""
    undertaking_fleet = jsonobject.JSONProperty('undertaking_fleet',
                                                value_type=list)
    """Fleet which is undertaking this mission. First element represents the
    order of the fleet, and the second holds the fleet name."""
    # TODO: Create Fleet object.
    eta = jsonobject.JSONProperty('eta', value_type=int)
    """Estimated Time of Arrival, in UNIX time with millisecond precision."""


class MissionList(model.KCAAObject):

    missions = jsonobject.JSONProperty('missions', [], value_type=list,
                                       element_type=Mission)
    """Mission instances."""

    def update(self, api_name, request, response, objects):
        super(MissionList, self).update(api_name, request, response, objects)
        if api_name == '/api_get_master/mission':
            self.update_api_get_master_mission(response)
        elif (api_name == '/api_get_member/deck' or
              api_name == '/api_get_member/deck_port'):
            self.update_api_get_member_deck(response)

    def update_api_get_master_mission(self, request, response):
        mission_to_fleet = {}
        for mission in self.missions:
            if mission.undertaking_fleet:
                mission_to_fleet[mission.id] = [mission.undertaking_fleet,
                                                mission.eta]
        missions = []
        for data in response['api_data']:
            mission_data = jsonobject.parse(data)
            mission = Mission(
                id=mission_data.api_id,
                name=mission_data.api_name,
                description=mission_data.api_details,
                difficulty=mission_data.api_difficulty,
                maparea=mission_data.api_maparea_id,
                state=mission_data.api_state,
                time=mission_data.api_time,
                consumption=resource.ResourcePercentage(
                    fuel=float(mission_data.api_use_fuel),
                    ammo=float(mission_data.api_use_bull)))
            fleet = mission_to_fleet.get(mission.id)
            if fleet:
                mission.undertaking_fleet = fleet[0]
                mission.eta = fleet[1]
            missions.append(mission)
        missions.sort(lambda x, y: x.id - y.id)
        self.missions = model.merge_list(self.missions, missions)

    def update_api_get_member_deck(self, request, response):
        mission_to_fleet = {}
        for data in response['api_data']:
            fleet_data = jsonobject.parse(data)
            if fleet_data.api_mission[0] != 0:
                mission_to_fleet[fleet_data.api_mission[1]] = [
                    fleet_data.api_id,
                    fleet_data.api_name,
                    fleet_data.api_mission[2]]
        for mission in self.missions:
            fleet = mission_to_fleet.get(mission.id)
            if fleet:
                mission.undertaking_fleet = fleet[:2]
                mission.eta = fleet[2]
                del mission_to_fleet[mission.id]
            else:
                mission.undertaking_fleet = None
                mission.eta = None
        # Create missions if it's not there yet. Otherwise undertaking_fleet
        # and eta will not be shown soon.
        if len(mission_to_fleet) > 0:
            for id, fleet in mission_to_fleet.iteritems():
                self.missions.append(Mission(
                    id=id,
                    undertaking_fleet=fleet[:2],
                    eta=fleet[2]))
            self.missions.sort(lambda x, y: x.id - y.id)
