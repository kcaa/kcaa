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
    generation = jsonobject.JSONProperty('generation', 0, value_type=int)
    """Generation of the current screen.

    This field starts with 0, and is incremented every time it detects a KCSAPI
    request that affects a screen transition.

    This value is incremented even if the transition makes :attr:`screen` being
    set to the same value as the last one.
    """

    api_sequence = []
    max_sequence_length = 10

    # This is best represented with TRIE. Rewrite if needed.
    API_SEQUENCE_TO_SCREEN_LIST = [
        (['/api_req_mission/result',
          '/api_get_member/deck_port'], screens.MISSION_RESULT),
    ]
    API_TO_SCREEN_MAP = {
        '/api_get_master/mapinfo': screens.PORT_EXPEDITION,
        '/api_get_master/mission': screens.PORT_MISSION,
        '/api_get_master/payitem': screens.PORT_ITEMSHOP,
        '/api_get_member/book2': screens.PORT_ENCYCLOPEDIA,
        '/api_get_member/deck_port': screens.PORT,
        '/api_get_member/practice': screens.PORT_PRACTICE,
        '/api_get_member/questlist': screens.PORT_QUESTLIST,
        '/api_req_mission/result': screens.MISSION_RESULT,
        '/api_req_practice/battle': screens.PRACTICE_BATTLE,
        '/api_req_practice/battle_result': screens.PRACTICE_BATTLERESULT,
        '/api_start': screens.SPECIAL_START,
    }

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


if __name__ == '__main__':
    import client_test
    client_test.main()
