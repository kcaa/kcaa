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
        '/api_get_master/mapinfo': screens.PORT_EXPEDITION,
        '/api_get_master/mission': screens.PORT_MISSION,
        '/api_get_master/payitem': screens.PORT_ITEMSHOP,
        '/api_get_member/book2': screens.PORT_ENCYCLOPEDIA,
        '/api_get_member/practice': screens.PORT_PRACTICE,
        '/api_get_member/questlist': screens.PORT_QUESTLIST,
        '/api_port/port': screens.PORT_MAIN,
        '/api_req_map/next': screens.EXPEDITION,  # TODO: special handler
        '/api_req_map/start': screens.EXPEDITION,  # TODO: special handler
        '/api_req_mission/result': screens.MISSION_RESULT,
        '/api_req_practice/battle': screens.PRACTICE_COMBAT,
        '/api_req_practice/battle_result': screens.PRACTICE_RESULT,
        '/api_req_sortie/battle': screens.EXPEDITION_COMBAT,
        '/api_req_sortie/battleresult': screens.EXPEDITION_RESULT,
        '/api_start2': screens.SPECIAL_START,
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


class ScheduleFragment(jsonobject.JSONSerializableObject):

    start = jsonobject.JSONProperty('start', value_type=int)
    """Start timing of this fragment, in seconds from the beginning of a
    day."""
    end = jsonobject.JSONProperty('end', value_type=int)
    """End timing of this fragment, in seconds from the beginning of a day."""


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
    auto_manipulators_enabled = jsonobject.JSONProperty(
        'auto_manipulators_enabled', value_type=bool)
    """True if auto manipulators are enabled."""
    auto_manipulators_active = jsonobject.JSONProperty(
        'auto_manipulators_active', value_type=bool)
    """True if auto manipulators are active."""
    auto_manipulators_schedules = jsonobject.JSONProperty(
        'auto_manipulators_schedules', [], value_type=list,
        element_type=ScheduleFragment)
    """Auto manipulators schedule."""


if __name__ == '__main__':
    import client_test
    client_test.main()
