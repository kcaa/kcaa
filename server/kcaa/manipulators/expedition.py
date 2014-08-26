#!/usr/bin/env python

import logging

import base
from kcaa import screens
from kcaa.kcsapi import mission


logger = logging.getLogger('kcaa.manipulators.expedition')


class GoOnExpedition(base.Manipulator):

    def run(self, fleet_id, maparea_id, map_id):
        fleet_id = int(fleet_id)
        maparea_id = int(maparea_id)
        map_id = int(map_id)
        logger.info('Making the fleet {} go on the expedition {}-{}'.format(
            fleet_id, maparea_id, map_id))
        # TODO: Move maparea definition to a separate module like kcsapic.
        if maparea_id > mission.Mission.MAPAREA_SOUTH:
            logger.error('Maparea {} is not supported.'.format(maparea_id))
        ship_list = self.objects.get('ShipList')
        if not ship_list:
            logger.error('No ship list was found. Giving up.')
            return
        fleet_list = self.objects.get('FleetList')
        if not fleet_list:
            logger.error('No fleet list was found. Giving up.')
            return
        fleet = fleet_list.fleets[fleet_id - 1]
        if fleet.mission_id is not None:
            logger.error('Fleet {} is undertaking mission {}.'.format(
                fleet.id, fleet.mission_id))
            return
        repair_dock = self.objects.get('RepairDock')
        if not repair_dock:
            logger.error('No repair dock was found. Giving up.')
            return
        for i, ship_id in enumerate(fleet.ship_ids):
            ship = ship_list.ships[str(ship_id)]
            if repair_dock.is_under_repair(ship_id):
                logger.error('Ship {} ({}) is under repair. Cannot proceed.'
                             .format(ship.name.encode('utf8'), i + 1))
                return
            if ship.hitpoint.current <= 0.5 * ship.hitpoint.maximum:
                logger.error('Ship {} ({}) has low hit point. Cannot proceed.'
                             .format(ship.name.encode('utf8'), i + 1))
                return
            if ship.vitality < 30:
                logger.error('Ship {} ({}) has low vitality. Cannot proceed.'
                             .format(ship.name.encode('utf8'), i + 1))
                return
        # Check ship slot and equipment slot requiement.
        yield self.screen.change_screen(screens.PORT_EXPEDITION)
        yield self.screen.select_maparea(maparea_id)
        yield self.screen.select_map(map_id)
        yield self.screen.try_expedition()
        yield self.screen.select_fleet(fleet_id)
        yield self.screen.confirm_expedition()
        # TODO: Yield to SailExpeditionMap.
