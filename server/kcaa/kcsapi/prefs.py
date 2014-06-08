#!/usr/bin/env python

import jsonobject
import model


class ScheduleFragment(jsonobject.JSONSerializableObject):

    start = jsonobject.JSONProperty('start', value_type=int)
    """Start timing of this fragment, in seconds from the beginning of a
    day."""
    end = jsonobject.JSONProperty('end', value_type=int)
    """End timing of this fragment, in seconds from the beginning of a day."""

    def __str__(self):
        return '(from {} to {})'.format(self.start, self.end)

    def __repr__(self):
        return str(self)


class AutoManipulatorPreferences(jsonobject.JSONSerializableObject):

    enabled = jsonobject.JSONProperty('enabled', False, value_type=bool)
    """True if auto manipulators are enabled.

    This controls all of the auto manipulators."""
    schedules = jsonobject.JSONProperty(
        'schedules', [ScheduleFragment(start=0, end=86400)],
        value_type=list, element_type=ScheduleFragment)
    """Auto manipulator schedules.

    TODO: Separate this per auto manipulator."""


class ShipRequirement(jsonobject.JSONSerializableObject):
    id = jsonobject.JSONProperty('id', value_type=int)
    """ID of the ship."""


class SavedFleet(jsonobject.JSONSerializableObject):
    name = jsonobject.JSONProperty('name', value_type=unicode)
    """Name of the fleet."""
    ship_requirements = jsonobject.JSONProperty(
        'ship_requirements', [], value_type=list, element_type=ShipRequirement)
    """Ship requirements."""


class FleetPreferences(jsonobject.JSONSerializableObject):
    saved_fleets = jsonobject.JSONProperty(
        'saved_fleets', [], value_type=list, element_type=SavedFleet)
    """Saved fleets."""


class Preferences(model.KCAAObject):
    """KCAA client preferences.

    This object serves as the central repository of user preferences.
    """

    automan_prefs = jsonobject.JSONProperty(
        'automan_prefs', AutoManipulatorPreferences(),
        value_type=AutoManipulatorPreferences)
    """Auto manipulator preferences."""
    fleet_prefs = jsonobject.JSONProperty(
        'fleet_prefs', FleetPreferences(), value_type=FleetPreferences)
    """Fleet preferences."""
