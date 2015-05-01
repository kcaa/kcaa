#!/usr/bin/env python

import logging

import jsonobject
import model


logger = logging.getLogger('kcaa.kcsapi.mapinfo')


class EventMapInfo(jsonobject.JSONSerializableObject):

    max_hitpoint = jsonobject.JSONProperty('max_hitpoint', value_type=int)
    """Maximum map HP."""
    hitpoint = jsonobject.JSONProperty('hitpoint', value_type=int)
    """Current map HP."""
    difficulty = jsonobject.JSONProperty('difficulty', value_type=int)
    """Difficulty rank selected by the player."""
    DIFFICULTY_UNSELECTED = 0
    DIFFICULTY_HEI = 1
    DIFFICULTY_OTSU = 2
    DIFFICULTY_KOU = 3
    state = jsonobject.JSONProperty('state', value_type=int)
    """State."""
    STATE_NEW = 1
    STATE_CLEARED = 2

    @staticmethod
    def create_from_data(data):
        return EventMapInfo(
            max_hitpoint=data.api_max_maphp,
            hitpoint=data.api_now_maphp,
            difficulty=data.api_selected_rank,
            state=data.api_state)


class MapInfo(jsonobject.JSONSerializableObject):

    id = jsonobject.ReadonlyJSONProperty('id', value_type=int)
    """ID."""
    name = jsonobject.ReadonlyJSONProperty('name', value_type=unicode)
    """Name."""
    operation_name = jsonobject.ReadonlyJSONProperty('operation_name',
                                                     value_type=unicode)
    """Operation name."""
    description = jsonobject.ReadonlyJSONProperty('description',
                                                  value_type=unicode)
    """Description."""
    maparea_id = jsonobject.ReadonlyJSONProperty('maparea_id', value_type=int)
    """Map area ID."""
    MAPAREA_BASE = 1
    MAPAREA_SOUTHWESTERN_ISLANDS = 2
    MAPAREA_NORTH = 3
    MAPAREA_WEST = 4
    MAPAREA_SOUTH = 5
    MAPAREA_MIDDLE = 6
    MAPAREA_2014_SPRING = 26
    MAPAREA_2014_SUMMER = 27
    MAPAREA_2015_SPRING = 30
    map_id = jsonobject.ReadonlyJSONProperty('map_id', value_type=int)
    """Map ID."""
    available = jsonobject.JSONProperty('available', value_type=bool)
    """Whether this map is available for expedition."""
    cleared = jsonobject.JSONProperty('cleared', value_type=bool)
    """Whether this map is cleared."""
    event_info = jsonobject.JSONProperty('event_info', value_type=EventMapInfo)
    """Event map specific info."""

    @staticmethod
    def create_from_master_data(data):
        return MapInfo(
            id=data.api_id,
            name=data.api_name,
            operation_name=data.api_opetext,
            description=data.api_infotext.replace('<br>', ''),
            maparea_id=data.api_maparea_id,
            map_id=data.api_no,
            available=False)


class MapInfoList(model.KCAAObject):

    maps = jsonobject.JSONProperty('maps', {}, value_type=dict,
                                   element_type=MapInfo)
    """Maps."""

    def get_map_by_id(self, maparea_id, map_id):
        # TODO: Generalize?
        if maparea_id == 'E':
            maparea_id = 30
        matched_maps = [mapinfo for mapinfo in self.maps.itervalues() if
                        mapinfo.maparea_id == maparea_id and
                        mapinfo.map_id == map_id]
        return matched_maps[0] if matched_maps else None

    def update(self, api_name, request, response, objects, debug):
        super(MapInfoList, self).update(api_name, request, response, objects,
                                        debug)
        if api_name == '/api_start2':
            for data in response.api_data.api_mst_mapinfo:
                self.maps[str(data.api_id)] = (
                    MapInfo.create_from_master_data(data))
        if api_name == '/api_get_member/mapinfo':
            for data in response.api_data:
                mapinfo = self.maps[str(data.api_id)]
                mapinfo.available = True
                mapinfo.cleared = data.api_cleared == 1
                if hasattr(data, 'api_eventmap'):
                    mapinfo.event_info = (
                        EventMapInfo.create_from_data(data.api_eventmap))
                # Other data that may be of interest:
                # - api_exboss_flag: Extra stage or not?
                # - api_defeat_count: Number of times the boss was defeated
