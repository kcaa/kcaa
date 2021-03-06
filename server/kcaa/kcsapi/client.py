#!/usr/bin/env python

import jsonobject
from kcaa import screens
import model


class Screen(model.KCAAObject):
    """Current screen.

    This object provides the best guess of the current screen that the client
    (Kancolle Flash player) is currently showing to the user.
    """

    screen = jsonobject.JSONProperty('screen', screens.UNKNOWN, value_type=int)
    """Current screen."""

    api_sequence = []
    max_sequence_length = 10

    # This is best represented with TRIE. Rewrite if needed.
    API_SEQUENCE_TO_SCREEN_LIST = [
        (['/api_req_mission/result',
          '/api_port/port'], screens.MISSION_RESULT),
    ]
    API_TO_SCREEN_MAP = {
        '/api_get_member/mapinfo': screens.PORT_EXPEDITION,
        '/api_get_member/mission': screens.PORT_MISSION,
        '/api_get_member/payitem': screens.PORT_ITEMSHOP,
        '/api_get_member/picture_book': screens.PORT_ENCYCLOPEDIA,
        '/api_get_member/practice': screens.PORT_PRACTICE,
        '/api_get_member/questlist': screens.PORT_QUESTLIST,
        '/api_get_member/record': screens.PORT_RECORD,
        '/api_port/port': screens.PORT_MAIN,
        '/api_req_battle_midnight/battle': screens.EXPEDITION_NIGHTCOMBAT,
        '/api_req_battle_midnight/sp_midnight': screens.EXPEDITION_NIGHTCOMBAT,
        '/api_req_combined_battle/battle': screens.EXPEDITION_COMBAT,
        '/api_req_combined_battle/battleresult': screens.EXPEDITION_RESULT,
        '/api_req_combined_battle/battle_water': screens.EXPEDITION_COMBAT,
        '/api_req_combined_battle/midnight_battle':
        screens.EXPEDITION_NIGHTCOMBAT,
        '/api_req_combined_battle/sp_midnight':
        screens.EXPEDITION_NIGHTCOMBAT,
        '/api_req_map/next': screens.EXPEDITION,
        '/api_req_map/start': screens.EXPEDITION,
        '/api_req_mission/result': screens.MISSION_RESULT,
        '/api_req_kaisou/powerup': screens.PORT_REBUILDING_REBUILDRESULT,
        '/api_req_kaisou/remodeling': screens.PORT_REBUILDING_REMODELRESULT,
        '/api_req_kousyou/createitem': screens.PORT_SHIPYARD_GETEQUIPMENT,
        '/api_req_kousyou/getship': screens.PORT_SHIPYARD_GETSHIP,
        '/api_req_practice/battle': screens.PRACTICE_COMBAT,
        '/api_req_practice/battle_result': screens.PRACTICE_RESULT,
        '/api_req_practice/midnight_battle': screens.PRACTICE_NIGHTCOMBAT,
        '/api_req_sortie/battle': screens.EXPEDITION_COMBAT,
        '/api_req_sortie/battleresult': screens.EXPEDITION_RESULT,
        '/api_start2': screens.SPECIAL_START,
    }

    @property
    def auto_generation(self):
        return False

    def update(self, api_name, request, response, objects, debug):
        super(Screen, self).update(api_name, request, response, objects, debug)
        self.api_sequence.append(api_name)
        del self.api_sequence[:-self.max_sequence_length]
        # Use the API sequence to guess the current screen.
        for sequence, screen in Screen.API_SEQUENCE_TO_SCREEN_LIST:
            if self.api_sequence[-len(sequence):] == sequence:
                self.screen = screen
                self.generation += 1
                return
        # Some API names are unique enough to identify the current screen.
        if api_name in Screen.API_TO_SCREEN_MAP:
            self.screen = Screen.API_TO_SCREEN_MAP[api_name]
            self.generation += 1


class RunningManipulators(model.KCAAObject):
    """Information about currently running manipulators.

    This is actually not an object represents KCSAPI-related information.
    Rather, this object is updated by :class:`ManipulatorManager`.
    """

    running_manipulator = jsonobject.JSONProperty('running_manipulator',
                                                  value_type=unicode)
    """Currently running manipulator."""
    manipulators_in_queue = jsonobject.JSONProperty(
        'manipulators_in_queue', [], value_type=list, element_type=unicode)
    """Manipulators waiting for execution in the queue."""
    auto_manipulators_active = jsonobject.JSONProperty(
        'auto_manipulators_active', value_type=bool)
    """True if auto manipulators are active."""


if __name__ == '__main__':
    import client_test
    client_test.main()
