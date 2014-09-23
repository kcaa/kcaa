#!/usr/bin/env python

import jsonobject
import model
import ship


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

    predicate = jsonobject.JSONProperty(
        'predicate', value_type=ship.ShipPredicate)
    """Predicate."""
    sorter = jsonobject.JSONProperty('sorter', value_type=ship.ShipSorter)
    """Sorter."""
    omittable = jsonobject.JSONProperty('omittable', False, value_type=bool)
    """Omittable.

    An omittable ship can be omitted if no ship meets the condition required in
    the predicate. A slot with the omitted ship is filled up with the ships
    following that slot.
    """


class SavedFleet(jsonobject.JSONSerializableObject):

    name = jsonobject.JSONProperty('name', value_type=unicode)
    """Name of the fleet."""
    global_predicate = jsonobject.JSONProperty(
        'global_predicate', value_type=ship.ShipPredicate)
    """Global predicate applied to all of ship selections.

    A global predicate is applied as AND operator for all ship selections
    defined here. This is usually used for selecting only available ships (no
    repair, no mission and not fatal etc.).
    """
    ship_requirements = jsonobject.JSONProperty(
        'ship_requirements', [], value_type=list, element_type=ShipRequirement)
    """Ship requirements."""

    def get_ships(self, ship_list):
        # TODO: Unit test.
        ships = []
        for ship_requirement in self.ship_requirements:
            predicate = ship_requirement.predicate
            if self.global_predicate:
                predicate = ship.ShipPredicate(and_=[
                    self.global_predicate, predicate])
            applicable_ships = [s for s in ship_list.ships.itervalues()
                                if predicate.apply(s)]
            ship_requirement.sorter.sort(applicable_ships)
            if not applicable_ships:
                if not ship_requirement.omittable:
                    return None
                ships.append(None)
            else:
                ships.append(applicable_ships[0])
        return [s for s in ships if s]


class FleetPreferences(jsonobject.JSONSerializableObject):
    saved_fleets = jsonobject.JSONProperty(
        'saved_fleets', [], value_type=list, element_type=SavedFleet)
    """Saved fleets."""


class PracticePlan(jsonobject.JSONSerializableObject):
    opponent_fleet_type = jsonobject.JSONProperty(
        'opponent_fleet_type', value_type=int)
    """Opponent fleet type."""
    fleet_name = jsonobject.JSONProperty('fleet_name', value_type=unicode)
    """Name of the fleet to go practice."""
    formation = jsonobject.JSONProperty('formation', value_type=int)
    """Formation."""
    FORMATION_SINGLE_LINE = 0
    FORMATION_DOUBLE_LINES = 1
    FORMATION_CIRCLE = 2
    FORMATION_LADDER = 3
    FORMATION_HORIZONTAL_LINE = 4


class PracticePreferences(jsonobject.JSONSerializableObject):

    practice_plans = jsonobject.JSONProperty(
        'practice_plans', [], value_type=list, element_type=PracticePlan)
    """Practice plans."""

    def get_practice_plan(self, opponent_fleet_type):
        practice_plans = filter(
            lambda p: (p.opponent_fleet_type == opponent_fleet_type and
                       p.fleet_name),
            self.practice_plans)
        if practice_plans:
            return practice_plans[0]


class MissionPlan(jsonobject.JSONSerializableObject):

    fleet_id = jsonobject.JSONProperty('fleet_id', value_type=int)
    """Fleet ID."""
    mission_id = jsonobject.JSONProperty('mission_id', value_type=int)
    """Mission ID."""
    fleet_name = jsonobject.JSONProperty('fleet_name', value_type=unicode)
    """Name of the fleet to go mission."""


class MissionPreferences(jsonobject.JSONSerializableObject):

    mission_plans = jsonobject.JSONProperty(
        'mission_plans', [], value_type=list, element_type=MissionPlan)
    """Mission plans."""

    def get_mission_plan(self, fleet_id):
        mission_plans = filter(
            lambda p: p.fleet_id == fleet_id, self.mission_plans)
        if mission_plans:
            return mission_plans[0]


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
    practice_prefs = jsonobject.JSONProperty(
        'practice_prefs', PracticePreferences(),
        value_type=PracticePreferences)
    """Practice preferences."""
    mission_prefs = jsonobject.JSONProperty(
        'mission_prefs', MissionPreferences(),
        value_type=MissionPreferences)

    def initialize(self):
        # TODO: Better rewrite this...
        opponent_fleet_types = frozenset(map(
            lambda p: p.opponent_fleet_type,
            self.practice_prefs.practice_plans))
        for opponent_fleet_type in xrange(8):
            if opponent_fleet_type not in opponent_fleet_types:
                self.practice_prefs.practice_plans.append(
                    PracticePlan(opponent_fleet_type=opponent_fleet_type,
                                 fleet_name=u'',
                                 formation=PracticePlan.FORMATION_SINGLE_LINE))
