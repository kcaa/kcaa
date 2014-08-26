#!/usr/bin/env python

import logging


logger = logging.getLogger('kcaa.manipulators.fleet')


def are_all_ships_available(manipulator, fleet_id):
    ship_list = manipulator.objects.get('ShipList')
    if not ship_list:
        logger.error('No ship list was found. Giving up.')
        return False
    fleet_list = manipulator.objects.get('FleetList')
    if not fleet_list:
        logger.error('No fleet list was found. Giving up.')
        return False
    fleet_ = fleet_list.fleets[fleet_id - 1]
    if fleet_.mission_id is not None:
        logger.error('Fleet {} is undertaking mission {}.'.format(
            fleet_.id, fleet_.mission_id))
        return False
    repair_dock = manipulator.objects.get('RepairDock')
    if not repair_dock:
        logger.error('No repair dock was found. Giving up.')
        return False
    for i, ship_id in enumerate(fleet_.ship_ids):
        ship = ship_list.ships[str(ship_id)]
        if repair_dock.is_under_repair(ship_id):
            logger.error('Ship {} ({}) is under repair. Cannot proceed.'
                         .format(ship.name.encode('utf8'), i + 1))
            return False
        if ship.hitpoint.current <= 0.5 * ship.hitpoint.maximum:
            logger.error('Ship {} ({}) has low hit point. Cannot proceed.'
                         .format(ship.name.encode('utf8'), i + 1))
            return False
        if ship.vitality < 30:
            logger.error('Ship {} ({}) has low vitality. Cannot proceed.'
                         .format(ship.name.encode('utf8'), i + 1))
            return False
    return True
