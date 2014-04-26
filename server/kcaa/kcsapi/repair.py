#!/usr/bin/env python

import jsonobject
import model


class RepairSlot(jsonobject.JSONSerializableObject):

    id = jsonobject.ReadonlyJSONProperty('id', value_type=int)
    """ID."""
    ship_id = jsonobject.JSONProperty('ship_id', value_type=int)
    """ID of ship being repaired in this slot."""
    eta = jsonobject.JSONProperty('eta', value_type=int)
    """Estimated Time of Arrival, in UNIX time with millisecond precision."""

    @property
    def in_use(self):
        return self.ship_id != 0


class RepairDock(model.KCAAObject):
    """Repair dock."""

    slots = jsonobject.JSONProperty('slots', [], value_type=list,
                                    element_type=RepairSlot)
    """Repair slots."""

    def update(self, api_name, request, response, objects, debug):
        super(RepairDock, self).update(api_name, request, response, objects,
                                       debug)
        if api_name == '/api_get_member/ndock':
            self.slots = []
            for data in response['api_data']:
                slot_data = jsonobject.parse(data)
                self.slots.append(RepairSlot(
                    id=slot_data.api_id,
                    ship_id=slot_data.api_ship_id,
                    eta=slot_data.api_complete_time))