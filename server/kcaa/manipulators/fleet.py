#!/usr/bin/env python

import logging


logger = logging.getLogger('kcaa.manipulators.fleet')


def classify_ships(manipulator, fleet_id, verbose=True):
    ship_list = manipulator.objects.get('ShipList')
    if not ship_list:
        if verbose:
            logger.error('No ship list was found. Giving up.')
        return False, [], []
    fleet_list = manipulator.objects.get('FleetList')
    if not fleet_list:
        if verbose:
            logger.error('No fleet list was found. Giving up.')
        return False, [], []
    fleet_ = fleet_list.fleets[fleet_id - 1]
    if fleet_.mission_id is not None:
        if verbose:
            logger.error('Fleet {} is undertaking mission {}.'.format(
                fleet_.id, fleet_.mission_id))
        return False, [], []
    good_ships, bad_ships = [], []
    for i, ship_id in enumerate(fleet_.ship_ids):
        ship = ship_list.ships[str(ship_id)]
        if ship.is_under_repair:
            bad_ships.append(ship)
            if verbose:
                logger.error('Ship {} ({}) is under repair. Cannot proceed.'
                             .format(ship.name.encode('utf8'), i + 1))
            continue
        if ship.hitpoint.current <= 0.5 * ship.hitpoint.maximum:
            bad_ships.append(ship)
            if verbose:
                logger.error('Ship {} ({}) has low hit point. Cannot proceed.'
                             .format(ship.name.encode('utf8'), i + 1))
            continue
        if ship.vitality < 30:
            bad_ships.append(ship)
            if verbose:
                logger.error('Ship {} ({}) has low vitality. Cannot proceed.'
                             .format(ship.name.encode('utf8'), i + 1))
            continue
        good_ships.append(ship)
    return True, good_ships, bad_ships


def are_all_ships_available(manipulator, fleet_id, verbose=True):
    ok, good_ships, bad_ships = classify_ships(manipulator, fleet_id, verbose)
    return ok and len(good_ships) > 0 and len(bad_ships) == 0
