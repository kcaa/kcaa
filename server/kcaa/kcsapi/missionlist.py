#!/usr/bin/env python

import numbers

import jsonobject
import model


class Mission(jsonobject.JSONSerializableObject):

    id = jsonobject.ReadonlyJSONProperty('id', 0, value_type=int)
    """ID."""
    name = jsonobject.ReadonlyJSONProperty('name', u'', value_type=unicode)
    """Name."""
    description = jsonobject.ReadonlyJSONProperty('description', u'',
                                                  value_type=unicode)
    """Description."""
    difficulty = jsonobject.ReadonlyJSONProperty('difficulty', 0,
                                                 value_type=int)
    """Difficulty."""
    DIFFICULTY_E = 1
    DIFFICULTY_D = 2
    DIFFICULTY_C = 3
    DIFFICULTY_B = 4
    DIFFICULTY_A = 5
    DIFFICULTY_S = 6
    DIFFICULTY_SS = 7
    DIFFICULTY_SSS = 8
    maparea = jsonobject.ReadonlyJSONProperty('maparea', 0, value_type=int)
    """Map area."""
    MAPAREA_BASE = 1
    MAPAREA_SOUTHWESTERN_ISLANDS = 2
    MAPAREA_NORTH = 3
    MAPAREA_WEST = 4
    MAPAREA_SOUTH = 5
    state = jsonobject.ReadonlyJSONProperty('state', 0, value_type=int)
    """State."""
    STATE_NEW = 0
    STATE_ACTIVE = 1
    STATE_COMPLETE = 2
    time = jsonobject.ReadonlyJSONProperty('time', 0, value_type=int)
    """Required time to complete in minutes."""
    ammo_consumption = jsonobject.ReadonlyJSONProperty(
        'ammo_consumption', 0, value_type=numbers.Number)
    """Ammo consumption relative to the fleet capacity. Ranges from 0 to 1."""
    oil_consumption = jsonobject.ReadonlyJSONProperty(
        'oil_consumption', 0, value_type=numbers.Number)
    """Oil consumption relative to the fleet capacity. Ranges from 0 to 1."""
    bonus_items = jsonobject.ReadonlyJSONProperty('bonus_items', None)
    """TODO: Bonus items?"""
    active = jsonobject.ReadonlyJSONProperty('active', 0, value_type=int)
    """TODO: Active?"""


class MissionList(model.KCAAObject):

    missions = jsonobject.JSONProperty('missions', [], value_type=list,
                                       element_type=Mission)
    """Mission instances."""

    def update(self, api_name, response):
        super(MissionList, self).update(api_name, response)
        missions = []
        for data in response['api_data']:
            mission_data = jsonobject.parse(data)
            missions.append(Mission(
                id=mission_data.api_id,
                name=mission_data.api_name,
                description=mission_data.api_details,
                difficulty=mission_data.api_difficulty,
                maparea=mission_data.api_maparea_id,
                state=mission_data.api_state,
                time=mission_data.api_time,
                ammo_consumption=mission_data.api_use_bull,
                oil_consumption=mission_data.api_use_fuel,
                active=mission_data.api_active))
        missions.sort(lambda x, y: x.id - y.id)
        self.missions = model.merge_list(self.missions, missions)
