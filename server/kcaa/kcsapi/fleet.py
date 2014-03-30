#!/usr/bin/env python

import jsonobject
import model


class Fleet(jsonobject.JSONSerializableObject):

    id = jsonobject.ReadonlyJSONProperty('id', value_type=int)
    """ID."""
    name = jsonobject.ReadonlyJSONProperty('name', value_type=unicode)
    """Name."""
    ship_ids = jsonobject.JSONProperty('ship_ids', value_type=list,
                                       element_type=int)
    """IDs of ships belonging to this fleet."""
    mission_id = jsonobject.JSONProperty('mission_id', value_type=int)
    """ID of mission which this fleet is undertaking."""
    mission_complete = jsonobject.JSONProperty('mission_complete',
                                               value_type=bool)
    """True if the mission is complete. Updated when the screen transitioned to
    PORT_MAIN."""


class FleetList(model.KCAAObject):
    """List of fleets (decks)."""

    fleets = jsonobject.JSONProperty('fleets', [], value_type=list,
                                     element_type=Fleet)
    """Fleets.

    Note that this list has 0-origin, while other objects use 1-origin index to
    reference a fleet."""

    def update(self, api_name, request, response, objects, debug):
        super(FleetList, self).update(api_name, request, response, objects,
                                      debug)
        if (api_name == '/api_get_member/deck' or
                api_name == '/api_get_member/deck_port'):
            self.fleets = []
            for data in response['api_data']:
                fleet_data = jsonobject.parse(data)
                mission_id = None
                mission_complete = None
                if fleet_data.api_mission[0] != 0:
                    mission_id = fleet_data.api_mission[1]
                    mission_complete = (
                        True if fleet_data.api_mission[3] == 1 else False)
                self.fleets.append(Fleet(
                    id=fleet_data.api_id,
                    name=fleet_data.api_name,
                    ship_ids=filter(lambda x: x != -1, fleet_data.api_ship),
                    mission_id=mission_id,
                    mission_complete=mission_complete))
        elif api_name == '/api_req_hensei/change':
            for i, data in enumerate(response['api_data']):
                self.fleets[i].ship_ids = filter(lambda x: x != -1, data)
