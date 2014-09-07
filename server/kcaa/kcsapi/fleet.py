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

    def find_fleet_for_ship(self, ship_id):
        for fleet in self.fleets:
            if ship_id in fleet.ship_ids:
                return fleet
        return None

    def update(self, api_name, request, response, objects, debug):
        super(FleetList, self).update(api_name, request, response, objects,
                                      debug)
        if api_name == '/api_port/port':
            self.update_fleets(response.api_data.api_deck_port)
        elif api_name == '/api_get_member/deck':
            self.update_fleets(response.api_data)
        elif api_name == '/api_get_member/ship3':
            self.update_fleets(response.api_data.api_deck_data)
        elif api_name == '/api_req_hensei/change':
            fleet = self.fleets[int(request.api_id)-1]
            ship_index = int(request.api_ship_idx)
            ship_id = int(request.api_ship_id)
            if ship_id == -1:
                # -1 means the ship was removed from the fleet.
                del fleet.ship_ids[ship_index]
            elif ship_id == -2:
                # -2 means all the ships except the flag ship were removed.
                del fleet.ship_ids[1:]
            elif ship_index >= len(fleet.ship_ids):
                fleet.ship_ids.append(ship_id)
            else:
                # First swap the ship if any.
                for another_fleet in self.fleets:
                    try:
                        old_index = another_fleet.ship_ids.index(ship_id)
                        another_fleet.ship_ids[old_index] = (
                            fleet.ship_ids[ship_index])
                        break
                    except ValueError:
                        pass
                fleet.ship_ids[ship_index] = ship_id

    def update_fleets(self, fleet_data):
        self.fleets = []
        for data in fleet_data:
            mission_id = None
            mission_complete = None
            if data.api_mission[0] != 0:
                mission_id = data.api_mission[1]
                # TODO: Fix this. This is not accurate.
                # Probably better to use Mission's eta and the current
                # time?
                mission_complete = data.api_mission[3] == 1
            self.fleets.append(Fleet(
                id=data.api_id,
                name=data.api_name,
                ship_ids=filter(lambda x: x != -1, data.api_ship),
                mission_id=mission_id,
                mission_complete=mission_complete))
