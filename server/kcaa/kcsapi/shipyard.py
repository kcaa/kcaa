#!/usr/bin/env python

import jsonobject
import model
import resource


class BuildSlot(jsonobject.JSONSerializableObject):

    id = jsonobject.ReadonlyJSONProperty('id', value_type=int)
    """ID."""
    ship_def_id = jsonobject.JSONProperty('ship_def_id', value_type=int)
    """ID of ship definition being repaired in this slot."""
    spent_resource = jsonobject.JSONProperty(
        'spent_resource', value_type=resource.Resource)
    """Resource used to bulid this ship."""
    material = jsonobject.JSONProperty('material', value_type=int)
    """Building material used to build this ship."""
    state = jsonobject.JSONProperty('state', value_type=int)
    """State of the slot."""
    STATE_EMPTY = 0
    STATE_BULIDING = 2
    STATE_COMPLETED = 3
    eta = jsonobject.JSONProperty('eta', value_type=long)
    """Estimated Time of Arrival, in UNIX time with millisecond precision."""

    @jsonobject.jsonproperty
    def empty(self):
        return self.state == BuildSlot.STATE_EMPTY

    def completed(self, now):
        return (not self.empty and
                (self.state == BuildSlot.STATE_COMPLETED or now >= self.eta))


class BuildDock(model.KCAAObject):
    """Build dock."""

    slots = jsonobject.JSONProperty('slots', [], value_type=list,
                                    element_type=BuildSlot)
    """Build slots."""

    @property
    def empty_slots(self):
        return [slot for slot in self.slots if slot.empty]

    def update(self, api_name, request, response, objects, debug):
        super(BuildDock, self).update(api_name, request, response, objects,
                                      debug)
        if api_name == '/api_get_member/kdock':
            self.update_slots(response.api_data)
        elif api_name == '/api_req_kousyou/getship':
            self.update_slots(response.api_data.api_kdock)
        elif api_name == '/api_req_kousyou/createship_speedchange':
            slot = self.slots[int(request.api_kdock_id) - 1]
            slot.state = BuildSlot.STATE_COMPLETED

    def update_slots(self, kdock_data):
        self.slots = []
        for data in kdock_data:
            if data.api_state == -1:
                # Not opened.
                continue
            self.slots.append(BuildSlot(
                id=data.api_id,
                ship_def_id=data.api_created_ship_id,
                spent_resource=resource.Resource(
                    fuel=data.api_item1,
                    ammo=data.api_item2,
                    steel=data.api_item3,
                    bauxite=data.api_item4),
                material=data.api_item5,
                state=data.api_state,
                eta=long(data.api_complete_time)))
