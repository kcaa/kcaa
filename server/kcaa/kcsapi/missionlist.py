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
    ID of the fleet, and the second holds the fleet name."""
    # Do not use fleet.Fleet here, as it yields another module dependency.
    eta = jsonobject.JSONProperty('eta', value_type=int)
    """Estimated Time of Arrival, in UNIX time with millisecond precision."""


class MissionList(model.KCAAObject):

    missions = jsonobject.JSONProperty('missions', [], value_type=list,
                                       element_type=Mission)
    """Mission instances."""

    def get_mission(self, mission_id):
        missions = filter(lambda mission: mission.id == mission_id,
                          self.missions)
        return missions[0] if missions else None

    def get_index_in_maparea(self, mission):
        missions_in_maparea = filter(lambda m: m.maparea == mission.maparea,
                                     self.missions)
        # I can't use list.index() as a /api_get_master/mission response will
        # be interleaved if the page is changed.
        # Here I assume the missions are sorted in ascending order of mission
        # ID, and they are contiguous.
        return mission.id - missions_in_maparea[0].id

    def update(self, api_name, request, response, objects, debug):
        super(MissionList, self).update(api_name, request, response, objects,
                                        debug)
        if api_name == '/api_get_master/mission':
            self.update_api_get_master_mission(request, response)
        elif (api_name == '/api_get_member/deck' or
              api_name == '/api_get_member/deck_port'):
            self.update_api_get_member_deck(request, response)

    def update_api_get_master_mission(self, request, response):
        mission_to_progress = {}
        for mission in self.missions:
            if mission.undertaking_fleet:
                mission_to_progress[mission.id] = [mission.undertaking_fleet,
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
            progress = mission_to_progress.get(mission.id)
            if progress:
                mission.undertaking_fleet = progress[0]
                mission.eta = progress[1]
            missions.append(mission)
        missions.sort(lambda x, y: x.id - y.id)
        self.missions = model.merge_list(self.missions, missions)

    def update_api_get_member_deck(self, request, response):
        mission_to_progress = {}
        for data in response['api_data']:
            fleet_data = jsonobject.parse(data)
            if fleet_data.api_mission[0] != 0:
                mission_id = fleet_data.api_mission[1]
                eta = fleet_data.api_mission[2]
                mission_to_progress[mission_id] = [
                    [fleet_data.api_id, fleet_data.api_name],
                    eta]
        for mission in self.missions:
            progress = mission_to_progress.get(mission.id)
            if progress:
                mission.undertaking_fleet = progress[0]
                mission.eta = progress[1]
                del mission_to_progress[mission.id]
            else:
                mission.undertaking_fleet = None
                mission.eta = None
        # Create missions if it's not there yet. Otherwise undertaking_fleet
        # and eta will not be shown soon.
        if len(mission_to_progress) > 0:
            for id, progress in mission_to_progress.iteritems():
                self.missions.append(Mission(
                    id=id,
                    name=u'N/A',
                    undertaking_fleet=progress[0],
                    eta=progress[1]))
            self.missions.sort(lambda x, y: x.id - y.id)
