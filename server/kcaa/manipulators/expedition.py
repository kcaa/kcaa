#!/usr/bin/env python

import logging

import base
import fleet
from kcaa import screens
from kcaa.kcsapi import expedition
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
        self.add_manipulator(SailOnExpeditionMap)


class SailOnExpeditionMap(base.Manipulator):

    def run(self):
        yield self.screen.wait_transition(screens.EXPEDITION, timeout=10.0)
        expedition_ = self.objects.get('Expedition')
        if not expedition:
            logger.error('No expedition info was found. Giving up.')
            return
        fleet_list = self.objects.get('FleetList')
        if not fleet_list:
            logger.error('No fleet list was found. Giving up.')
            return
        if expedition_.needs_compass:
            self.screen.update_screen_id(screens.EXPEDITION_COMPASS)
            yield self.screen.roll_compass()
        # Save the current info early not to be overwritten.
        event = expedition_.event
        is_terminal = expedition_.is_terminal
        self.screen.update_screen_id(screens.EXPEDITION_SAILING)
        # TODO: Handle a special sailing animation (e.g. spotter aircraft), if
        # needed. Expedition object should have such information.
        yield 4.0
        if event in (expedition.Expedition.EVENT_BATTLE,
                     expedition.Expedition.EVENT_BATTLE_BOSS):
            yield 2.0
            # TODO: Is this usable for expedition too?
            fleet = fleet_list.fleets[expedition_.fleet_id - 1]
            if len(fleet.ship_ids) >= 4:
                yield self.screen.select_formation(self.choose_formation())
            # TODO: Yield to EngageExpedition.
            return
        if is_terminal:
            self.screen.update_screen_id(screens.EXPEDITION_TERMINAL)
            yield self.screen.proceed_terminal_screen()
            return
        # This cell is a nonterminal cell without a battle. The next KCSAPI
        # /api_req_map/next should be received. Iterate on.
        self.add_manipulator(SailOnExpeditionMap)

    def choose_formation(self):
        # TODO: Make a smarter decision.
        return 0
