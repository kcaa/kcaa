#!/usr/bin/env python

import logging

import base
import fleet
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
        if not fleet.are_all_ships_available(self, fleet_id):
            return
        # Check ship slot and equipment slot requiement.
        yield self.screen.change_screen(screens.PORT_EXPEDITION)
        yield self.screen.select_maparea(maparea_id)
        yield self.screen.select_map(map_id)
        yield self.screen.try_expedition()
        yield self.screen.select_fleet(fleet_id)
        yield self.screen.confirm_expedition()
        # TODO: Yield to SailExpeditionMap.
