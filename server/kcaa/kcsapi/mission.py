#!/usr/bin/env python

import jsonobject
import model
import resource


# Rewards obtained on success, which is not available in KCSAPI response.
# Cited from: http://wikiwiki.jp/kancolle/?%B1%F3%C0%AC
# TODO: Move this out to some configuration file, possibly in JSON?
MISSION_REWARDS = {
    # MAPAREA_BASE
    1: resource.Resource(ammo=30),
    2: resource.Resource(ammo=100, steel=30),
    3: resource.Resource(fuel=30, ammo=30, steel=40),
    4: resource.Resource(ammo=60),
    5: resource.Resource(fuel=200, ammo=200, steel=20, bauxite=20),
    6: resource.Resource(bauxite=80),
    7: resource.Resource(steel=50, bauxite=50),
    8: resource.Resource(fuel=50, ammo=100, steel=50, bauxite=50),
    # MAPAREA_SOUTHWESTERN_ISLANDS
    9: resource.Resource(fuel=350),
    10: resource.Resource(ammo=50, bauxite=30),
    11: resource.Resource(bauxite=250),
    12: resource.Resource(fuel=50, ammo=250, steel=200, bauxite=50),
    13: resource.Resource(fuel=240, ammo=300),
    14: resource.Resource(ammo=240, steel=200),
    15: resource.Resource(steel=300, bauxite=400),
    16: resource.Resource(fuel=500, ammo=500, steel=200, bauxite=200),
    # MAPAREA_NORTH
    17: resource.Resource(fuel=70, ammo=70, steel=50),
    18: resource.Resource(steel=300, bauxite=100),
    19: resource.Resource(fuel=400, steel=50, bauxite=30),
    20: resource.Resource(steel=150),
    21: resource.Resource(fuel=320, ammo=270),
    22: resource.Resource(ammo=10),
    23: resource.Resource(ammo=20, bauxite=100),
    # MAPAREA_WEST
    25: resource.Resource(fuel=900, steel=500),
    26: resource.Resource(bauxite=900),
    27: resource.Resource(steel=800),
    28: resource.Resource(steel=900, bauxite=350),
    29: resource.Resource(bauxite=100),
    30: resource.Resource(bauxite=100),
    31: resource.Resource(ammo=30),
    # MAPAREA_SOUTH
    33: resource.Resource(),
    34: resource.Resource(),
    35: resource.Resource(steel=240, bauxite=280),
    36: resource.Resource(fuel=480, steel=200, bauxite=200),
    37: resource.Resource(ammo=380, steel=270),
    38: resource.Resource(fuel=420, steel=200),
}


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
    MAPAREA_2014_SPRING = 26
    MAPAREA_2014_SUMMER = 27
    state = jsonobject.JSONProperty('state', value_type=int)
    """State."""
    STATE_NEW = 0
    STATE_ACTIVE = 1
    STATE_COMPLETE = 2
    time = jsonobject.ReadonlyJSONProperty('time', value_type=int)
    """Required time to complete in minutes."""
    consumption = jsonobject.ReadonlyJSONProperty(
        'consumption', value_type=resource.ResourcePercentage)
    """Resource consumption percentage relative to the fleet capacity."""
    rewards = jsonobject.ReadonlyJSONProperty('rewards',
                                              value_type=resource.Resource)
    """Rewards obtained on success."""
    bonus_items = jsonobject.ReadonlyJSONProperty('bonus_items')
    """TODO: Bonus items?"""
    undertaking_fleet = jsonobject.JSONProperty('undertaking_fleet',
                                                value_type=list)
    """Fleet which is undertaking this mission. First element represents the
    ID of the fleet, and the second holds the fleet name."""
    # Do not use fleet.Fleet here, as it yields another module dependency.
    eta = jsonobject.JSONProperty('eta')
    """Estimated Time of Arrival, in UNIX time with millisecond precision.

    Do not set the value type; this may be typed as int by Linux json loader
    while as long by Windows one. This poses a tricky problem when reloading
    this module. Better not to stick with a strict type check for now."""


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
        if api_name == '/api_start2':
            self.update_master(request, response)
        elif api_name == '/api_get_member/mission':
            self.update_api_get_member_mission(request, response)
        elif api_name == '/api_get_member/deck':
            self.update_mission_fleets(response.api_data)
        elif api_name == '/api_port/port':
            self.update_mission_fleets(response.api_data.api_deck_port)

    def update_master(self, request, response):
        # TODO: Refactor this method. As the master information is now shipped
        # with /api_start2, there's no need to care if there is already a
        # member data there.
        mission_to_progress = {}
        for mission in self.missions:
            if mission.undertaking_fleet:
                mission_to_progress[mission.id] = [mission.undertaking_fleet,
                                                   mission.eta]
        missions = []
        for data in response.api_data.api_mst_mission:
            mission = Mission(
                id=data.api_id,
                name=data.api_name,
                description=data.api_details,
                difficulty=data.api_difficulty,
                maparea=data.api_maparea_id,
                state=Mission.STATE_COMPLETE,
                time=data.api_time,
                consumption=resource.ResourcePercentage(
                    fuel=float(data.api_use_fuel),
                    ammo=float(data.api_use_bull)),
                rewards=MISSION_REWARDS.get(data.api_id, {}))
            progress = mission_to_progress.get(mission.id)
            if progress:
                mission.undertaking_fleet = progress[0]
                mission.eta = progress[1]
            missions.append(mission)
        missions.sort(lambda x, y: x.id - y.id)
        self.missions = model.merge_list(self.missions, missions)

    def update_api_get_member_mission(self, request, response):
        mission_to_state = {}
        for data in response.api_data:
            mission_to_state[data.api_mission_id] = data.api_state
        for mission in self.missions:
            mission.state = mission_to_state.get(
                mission.id, Mission.STATE_COMPLETE)

    def update_mission_fleets(self, fleet_data):
        # TODO: Refactor this method. As the master information is now shipped
        # with /api_start2, there's no need to care if there is already a
        # member data there.
        mission_to_progress = {}
        for data in fleet_data:
            if data.api_mission[0] != 0:
                mission_id = data.api_mission[1]
                eta = long(data.api_mission[2])
                mission_to_progress[mission_id] = [
                    [data.api_id, data.api_name], eta]
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
                    undertaking_fleet=progress[0],
                    eta=progress[1]))
            self.missions.sort(lambda x, y: x.id - y.id)
