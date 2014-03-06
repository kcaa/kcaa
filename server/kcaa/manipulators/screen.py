#!/usr/bin/env python

import logging

from kcaa import screens


class Screen(object):

    def __init__(self, manager):
        self._logger = logging.getLogger('kcaa.manipulators.screen')
        self.manager = manager

    def do_task(self, t, *args, **kwargs):
        return self.manager.add_task(t, *args, **kwargs)

    def click(self, x, y):
        self.manager.click(x, y)

    @property
    def screen_id(self):
        screen_object = self.manager.objects.get('Screen')
        if screen_object:
            return screen_object.screen
        else:
            return None

    @property
    def screen_generation(self):
        screen_object = self.manager.objects.get('Screen')
        if screen_object:
            return screen_object.generation
        else:
            return 0

    def update_screen_id(self, screen_id):
        """Update screen ID explicitly.

        This method explicitly updates the screen ID maintained by
        :class:`kcaa.kcsapi.client.Screen`. This is not required if the screen
        transition can be detected by it (like port to quest list screen), but
        necessary if the client doesn't sent any requests.
        """
        self.manager.objects['Screen'].screen = screen_id
        self.manager.updated_object_types.add('Screen')

    def assert_screen(self, screen_id):
        if self.screen_id != screen_id:
            raise TypeError(
                'This operation cannot be done. Expected: {}, Current: {}'
                .format(screen_id, self.screen_id))

    def assert_screen_category(self, screen_id):
        if not screens.in_category(self.screen_id, screen_id):
            raise TypeError(
                'This operation cannot be done. Expected category: {}, '
                'Current: {}'.format(screen_id, self.screen_id))

    def transition_to(self, screen_id, delay=3.0):
        def transition_to_task(task):
            yield delay
            self.update_screen_id(screen_id)
            yield task.unit
        return self.do_task(transition_to_task)

    def wait_transition(self, screen_id, timeout=5.0, raise_on_timeout=True,
                        buffer_delay=1.0):
        """Wait until the screen transition."""
        def wait_transition_task(task):
            while self.screen_id != screen_id:
                if task.time > timeout:
                    if raise_on_timeout:
                        raise ValueError(
                            'Cannot transition from screen {} to screen {}'.
                            format(self.screen_id, screen_id))
                    return
                yield task.unit
            yield buffer_delay
        return self.do_task(wait_transition_task)

    def change_screen(self, screen_id):
        """Change the screen."""
        self.raise_impossible_transition(screen_id)

    def raise_impossible_transition(self, screen_id):
        raise TypeError('Cannot change screen from {} to {}'.format(
            self.screen_id, screen_id))


class StartScreen(Screen):

    def proceed(self):
        def proceed_task(task):
            self.click(620, 400)
            yield self.wait_transition(screens.PORT, timeout=20.0)
        self.assert_screen(screens.SPECIAL_START)
        return self.do_task(proceed_task)


class PortScreen(Screen):

    def click_port_button(self):
        self.click(50, 50)

    def click_back_button(self):
        self.click(60, 450)

    def click_attack_button(self):
        # TODO: Move this to PortMainScreen. Use some other button (record?)
        # instead in check_mission_result.
        self.click(200, 270)

    def click_somewhere(self):
        self.click(790, 10)

    def change_screen(self, screen_id):
        # If the current screen is unknown, go first to the port main screen,
        # and then move to the target screen.
        def change_screen_task(task):
            last_generation = self.screen_generation
            self.click_port_button()
            yield 2.0
            if self.screen_generation == last_generation:
                # If this is the case, we were at the port main screen or at
                # some undetectable screen missing 'Port' button.
                self.click_back_button()
            yield self.wait_transition(screens.PORT)
            self.update_screen_id(screens.PORT_MAIN)
            yield task.unit
            yield self.manager.current_screen.change_screen(screen_id)
        self.assert_screen_category(screens.PORT)
        return self.do_task(change_screen_task)

    def check_mission_result(self):
        def check_mission_result_task(task):
            # First, ensure we are at the port main screen.
            self._logger.debug('Changing to the port main screen.')
            if self.screen_id == screens.PORT:
                self._logger.debug(
                    'This is port screen. Clicking port and back buttons.')
                self.click_port_button()
                yield 2.0
                self.click_back_button()
                yield 5.0
                if self.screen_id == screens.PORT_MISSION_RESULT:
                    self._logger.debug('Changed to the mission result screen.')
                    yield (self.manager.current_screen.
                           proceed_mission_result_screen())
                    return
                self._logger.debug('Are we still at the port main screen?')
            else:
                self._logger.debug('Trying to change screen to port main.')
                yield self.change_screen(screens.PORT_MAIN)
                self._logger.debug('We should be at the port main screen.')
            # If not, there are 2 possibilities:
            # - currently the client is at the port main screen and aware
            #   of the completed mission.
            # - the client has been at the port main screen without knowing
            #   there is a completed mission.
            self._logger.debug('Now at the port main screen, clicking.')
            self.click_attack_button()
            yield 5.0
            if self.screen_id == screens.PORT_MISSION_RESULT:
                self._logger.debug('Reached mission result screen.')
                yield (self.manager.current_screen.
                       proceed_mission_result_screen())
                return
            else:
                self._logger.debug('Now we should be at attack selection '
                                   'screen. Getting back to the main.')
                self.click_port_button()
                yield 2.0
                self.click_somewhere()
                yield 5.0
                self._logger.debug('Clicked twice...')
                if self.screen_id == screens.PORT_MISSION_RESULT:
                    self._logger.debug('Finally we are aware.')
                    yield (self.manager.current_screen.
                           proceed_mission_result_screen())
                    return
                else:
                    self._logger.info('Failed to detect the screen.')
        return self.do_task(check_mission_result_task)


class PortMainScreen(PortScreen):

    def click_logistics_button(self):
        self.click(80, 225)

    def change_screen(self, screen_id):
        def change_screen_task(task):
            if screen_id == screens.PORT_MAIN:
                yield 0.0
            elif screen_id == screens.PORT_LOGISTICS:
                self.click_logistics_button()
                yield self.transition_to(screens.PORT_LOGISTICS)
            else:
                self.raise_impossible_transition(screen_id)
        self.assert_screen(screens.PORT_MAIN)
        return self.do_task(change_screen_task)


class PortMissionResultScreen(PortScreen):

    def proceed_mission_result_screen(self):
        def proceed_mission_result_screen_task(task):
            self.assert_screen(screens.PORT_MISSION_RESULT)
            self._logger.debug('This is mission result screen; clicking.')
            yield 5.0
            self.click_somewhere()
            yield 2.0
            self.update_screen_id(screens.PORT_MAIN)
            yield task.unit
        return self.do_task(proceed_mission_result_screen_task)


class PortOperationsScreen(PortScreen):
    pass


class PortLogisticsScreen(PortOperationsScreen):

    def change_screen(self, screen_id):
        def change_screen_task(task):
            if screen_id == screens.PORT_LOGISTICS:
                yield 0.0
            else:
                self.raise_impossible_transition(screen_id)
        self.assert_screen(screens.PORT_LOGISTICS)
        return self.do_task(change_screen_task)

    def select_fleet(self, fleet_id):
        def select_fleet_task(task):
            self.click(120 + 30 * fleet_id, 120)
            yield 1.0
        return self.do_task(select_fleet_task)

    def select_ship_list(self):
        def select_ship_list_task(task):
            self.click(270, 120)
            yield 1.0
        return self.do_task(select_ship_list_task)

    def select_all_members(self):
        def select_all_members_task(task):
            self.click(120, 120)
            yield 2.0
        return self.do_task(select_all_members_task)

    def charge_both(self):
        def charge_both_task(task):
            self.click(705, 445)
            yield 5.0
        return self.do_task(charge_both_task)
