#!/usr/bin/env python

import logging
import time
import traceback

import mission
from kcaa import screens
from kcaa import kcsapi


class Screen(object):

    def __init__(self, manager):
        self._logger = logging.getLogger('kcaa.manipulators.screen')
        self.manager = manager

    def do_task(self, t, *args, **kwargs):
        return self.manager.add_task(t, *args, **kwargs)

    def click(self, x, y):
        caller_names = []
        for callsite_info in reversed(traceback.extract_stack(limit=3)[:-1]):
            caller_names.append(callsite_info[2])
        self._logger.debug('Mouse click at {}, {} ({})'.format(
            x, y, ' <- '.join(caller_names)))
        self.manager.click(x, y)

    def click_hold(self, x, y):
        callsite_info = traceback.extract_stack()[-2]
        caller_name = callsite_info[2]
        self._logger.debug('Mouse click and hold at {}, {} ({})'.format(
            x, y, caller_name))
        self.manager.click_hold(x, y)

    def click_release(self, x, y):
        callsite_info = traceback.extract_stack()[-2]
        caller_name = callsite_info[2]
        self._logger.debug('Mouse release at {}, {} ({})'.format(
            x, y, caller_name))
        self.manager.click_release(x, y)

    def move_mouse(self, x, y):
        callsite_info = traceback.extract_stack()[-2]
        caller_name = callsite_info[2]
        self._logger.debug('Mouse move to {}, {} ({})'.format(
            x, y, caller_name))
        self.manager.move_mouse(x, y)

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
        necessary if the client doesn't send any requests.
        """
        self.manager.update_screen(screen_id)

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
            # Allow auto manipulators to trigger when its precondition is that
            # the screen ID matches to screen_id. E.g. AutoChargeFleet triggers
            # after the screen transitioned to PORT_MAIN. This 1 unit time
            # delay allows that high priority task to interrupt.
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

    def click_somewhere(self):
        self.click(790, 10)


class StartScreen(Screen):

    def proceed(self):
        def proceed_task(task):
            self.click(620, 400)
            yield self.wait_transition(screens.PORT_MAIN, timeout=20.0,
                                       buffer_delay=3.0)
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

    def click_record_button(self):
        def click_record_button_task(task):
            self.click(165, 50)
            yield 2.0
        return self.do_task(click_record_button_task)

    def click_encyclopedia_button(self):
        def click_encyclopedia_button_task(task):
            self.click(320, 50)
            yield 2.0
        return self.do_task(click_encyclopedia_button_task)

    def click_itemrack_button(self):
        def click_itemrack_button_task(task):
            self.click(400, 50)
            yield 2.0
        return self.do_task(click_itemrack_button_task)

    def click_furniture_button(self):
        def click_furniture_button_task(task):
            self.click(485, 50)
            yield 2.0
        return self.do_task(click_furniture_button_task)

    def click_quest_button(self):
        def click_quest_button_task(task):
            self.click(560, 50)
            yield self.wait_transition(screens.PORT_QUESTLIST)
            self.click_somewhere()
            yield 2.0
        return self.do_task(click_quest_button_task)

    def click_item_shop_button(self):
        def click_item_shop_button_task(task):
            self.click(615, 50)
            yield 2.0
        return self.do_task(click_item_shop_button_task)

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
            yield 3.0
            if self.screen_id == screens.PORT:
                self.update_screen_id(screens.PORT_MAIN)
            yield self.manager.current_screen.change_screen(screen_id)
        self.assert_screen_category(screens.PORT)
        return self.do_task(change_screen_task)

    def check_mission_results_if_any(self):
        # This is a kind of unauthorized act; but it is really nasty to
        # encounter a mission result screen when disabling the auto
        # manipulators.
        # NOTE: This may be problematic when mission.py starts to import
        # screen.py. Consider extracting the mission check logic to screen.py
        # if that happens.
        def check_mission_results_if_any_task(task):
            mission_list = self.manager.objects['MissionList']
            now = long(1000 * time.time())
            count, wait = mission.AutoCheckMissionResult.check_missions(
                mission_list, now)
            if count == 0:
                return
            self._logger.debug(
                'There are {} missions. Checking them first.'.format(count))
            yield wait
            for _ in xrange(count):
                yield self.check_mission_result()
            # Do not run logistics.ChargeAllFleets. It would complicate things,
            # and logistics.AutoChargeFleet will take care of it if enabled.
        return self.do_task(check_mission_results_if_any_task)

    def check_mission_result(self):
        def check_mission_result_task(task):
            # First, ensure we are at the port main screen.
            if self.screen_id == screens.PORT:
                self._logger.debug(
                    'This is port screen. Clicking port and back buttons.')
                self.click_port_button()
                yield 2.0
                self.click_back_button()
                yield 5.0
                if self.screen_id == screens.MISSION_RESULT:
                    self._logger.debug('Changed to the mission result screen.')
                    yield (self.manager.current_screen.
                           proceed_mission_result_screen())
                    return
                self._logger.debug('Are we still at the port main screen?')
            elif self.screen_id == screens.PORT_MAIN:
                # Do not do anything if already on port main.
                # This is required if called from check_mission_results_if_any.
                pass
            else:
                self._logger.debug('Trying to change screen to port main.')
                yield self.change_screen(screens.PORT_MAIN)
                self._logger.debug('We should be at the port main screen.')
            # If we reach here, there are 2 possibilities:
            # - currently the client is at the port main screen and aware
            #   of the completed mission.
            # - the client has been at the port main screen without knowing
            #   there is a completed mission.
            self._logger.debug('Now at the port main screen, clicking.')
            self.click_attack_button()
            yield 5.0
            if self.screen_id == screens.MISSION_RESULT:
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
                if self.screen_id == screens.MISSION_RESULT:
                    self._logger.debug('Finally we are aware.')
                    yield (self.manager.current_screen.
                           proceed_mission_result_screen())
                    return
                else:
                    self._logger.info('Failed to detect the screen.')
        return self.do_task(check_mission_result_task)


class PortMainScreen(PortScreen):

    def change_screen(self, screen_id):
        screen_map = {
            screens.PORT_ORGANIZING: self.click_organizing_button,
            screens.PORT_LOGISTICS: self.click_logistics_button,
            screens.PORT_REBUILDING: self.click_rebuilding_button,
            screens.PORT_REPAIR: self.click_repair_button,
            screens.PORT_SHIPYARD: self.click_shipyard_button,
            # These screens are available from port operation screens, but not
            # necessarily for others like the encyclopedia. To simplify the
            # scenario, we always get back to the port main before clicking
            # those buttons.
            screens.PORT_RECORD: self.click_record_button,
            screens.PORT_ENCYCLOPEDIA: self.click_encyclopedia_button,
            screens.PORT_ITEMRACK: self.click_itemrack_button,
            screens.PORT_FURNITURE: self.click_furniture_button,
            screens.PORT_QUESTLIST: self.click_quest_button,
            screens.PORT_ITEMSHOP: self.click_item_shop_button,
        }

        def change_screen_task(task):
            yield self.check_mission_results_if_any()
            if screen_id == screens.PORT_MAIN:
                yield 0.0
                return
            elif screen_id == screens.PORT_EXPEDITION:
                self.click_attack_button()
                yield 2.0
                self.click_expedition_button()
                yield self.wait_transition(screens.PORT_EXPEDITION)
                return
            elif screen_id == screens.PORT_PRACTICE:
                self.click_attack_button()
                yield 2.0
                self.click_practice_button()
                yield self.wait_transition(screens.PORT_PRACTICE)
                return
            elif screen_id == screens.PORT_MISSION:
                self.click_attack_button()
                yield 2.0
                self.click_mission_button()
                yield self.wait_transition(screens.PORT_MISSION)
                return
            if screen_id in screen_map:
                screen_map[screen_id]()
                yield self.transition_to(screen_id)
            else:
                self.raise_impossible_transition(screen_id)
        self.assert_screen(screens.PORT_MAIN)
        return self.do_task(change_screen_task)

    def click_expedition_button(self):
        self.click(230, 230)

    def click_practice_button(self):
        self.click(455, 230)

    def click_mission_button(self):
        self.click(680, 230)

    def click_organizing_button(self):
        self.click(200, 140)

    def click_logistics_button(self):
        self.click(80, 225)

    def click_rebuilding_button(self):
        self.click(320, 225)

    def click_repair_button(self):
        self.click(125, 365)

    def click_shipyard_button(self):
        self.click(275, 365)


class PortQuestScreen(PortScreen):

    def __init__(self, manager):
        super(PortQuestScreen, self).__init__(manager)
        self._current_page = 1

    @property
    def current_page(self):
        return self._current_page

    def wait_quest_update(self, last_generation):
        def wait_quest_update_task(task):
            while self.screen_generation == last_generation:
                yield task.unit
            yield 0.5
        return self.do_task(wait_quest_update_task)

    def select_page(self, page, max_page):
        def select_page_task(task):
            # This select_page() is a bit different from other select_page()
            # implementations.
            # - The next button in the bottom just advances one by one instead
            #   of jumping by 5.
            # - Each page transition involves networking.
            if page == self._current_page:
                return
            if page == max_page:
                last_generation = self.screen_generation
                self.click_page_last()
                yield self.wait_quest_update(last_generation)
                self.current_page = page
                return
            last_generation = self.screen_generation
            self.click_page_reset()
            yield self.wait_quest_update(last_generation)
            if page == 1:
                self.current_page = page
                return
            if page <= 5:
                last_generation = self.screen_generation
                self.click_page(page - 1)
                yield self.wait_quest_update(last_generation)
                self.current_page = page
                return
            last_generation = self.screen_generation
            self.click_page(4)
            yield self.wait_quest_update(last_generation)
            current_page = 5
            while page - current_page >= 2:
                last_generation = self.screen_generation
                self.click_page_next_2()
                current_page += 2
                yield self.wait_quest_update(last_generation)
            while page > current_page:
                last_generation = self.screen_generation
                self.click_page_next()
                current_page += 1
                yield self.wait_quest_update(last_generation)
            self._current_page = page
        return self.do_task(select_page_task)

    def click_page(self, position):
        # position ranges from 0 to 4.
        self.click(355 + 52 * position, 465)

    def click_page_reset(self):
        self.click(265, 465)

    def click_page_last(self):
        self.click(655, 450)

    def click_page_next(self):
        self.click_page(3)

    def click_page_next_2(self):
        self.click_page(4)

    def click_next_page_button(self):
        def click_next_page_button_task(task):
            last_generation = self.screen_generation
            self.click(620, 465)
            yield self.wait_quest_update(last_generation)
        return self.do_task(click_next_page_button_task)


class PortExpeditionScreen(PortScreen):

    def change_screen(self, screen_id):
        def change_screen_task(task):
            if screen_id == screens.PORT_EXPEDITION:
                yield 0.0
                return
            yield super(PortExpeditionScreen, self).change_screen(screen_id)
            # TODO: This is a boilerplate. Consider to extract as a method.
            if self.screen_id == screen_id:
                return
            else:
                self.raise_impossible_transition(screen_id)
        return self.do_task(change_screen_task)

    def select_maparea(self, maparea_id):
        def select_maparea_task(task):
            if maparea_id == 'E':
                self.click(715, 440)
            else:
                self.click(80 + 75 * maparea_id, 440)
            yield 1.0
        return self.do_task(select_maparea_task)

    def select_map(self, maparea_id, map_id):
        def select_map_task(task):
            # TODO: Generalize?
            # TODO: Abort when the difficulty has not been selected?
            if maparea_id == 'E':
                # 2015 Spring
                if map_id <= 4:
                    self.click(560, 98 + 72 * map_id)
                    yield 2.0
                    if map_id == 1:
                        yield self.dismiss_event_notification()
                else:
                    # 2015 Spring
                    self.click(440, 280)
                    yield 1.0
                    self.click(560, 215 + 145 * (map_id - 5))
                    yield 2.0
                yield self.dismiss_event_notification()
            else:
                if map_id <= 4:
                    x = 285 + 340 * ((map_id - 1) % 2)
                    y = 210 + 140 * ((map_id - 1) / 2)
                    self.click(x, y)
                    yield 2.0
                else:
                    self.click(785, 280)
                    yield 1.0
                    self.click(450, 210 + 140 * (map_id - 5))
                    yield 2.0
        return self.do_task(select_map_task)

    def try_expedition(self):
        def try_expedition_task(task):
            self.click(690, 445)
            yield 2.0
        return self.do_task(try_expedition_task)

    def select_fleet(self, fleet_id):
        def select_fleet_task(task):
            self.click(335 + 30 * fleet_id, 120)
            yield 1.0
        return self.do_task(select_fleet_task)

    def confirm_expedition(self):
        def confirm_expedition_task(task):
            self.click(635, 445)
            yield 7.0
        return self.do_task(confirm_expedition_task)

    def dismiss_event_notification(self):
        def dismiss_event_notification_task(task):
            self.click(650, 240)
            yield 2.0
        return self.do_task(dismiss_event_notification_task)


class PortPracticeScreen(PortScreen):

    def change_screen(self, screen_id):
        def change_screen_task(task):
            if screen_id == screens.PORT_PRACTICE:
                yield 0.0
                return
            yield super(PortPracticeScreen, self).change_screen(screen_id)
            # TODO: This is a boilerplate. Consider to extract as a method.
            if self.screen_id == screen_id:
                return
            else:
                self.raise_impossible_transition(screen_id)
        return self.do_task(change_screen_task)

    def check_opponent(self, practice_id):
        def check_opponent_task(task):
            self.click(720, 145 + 55 * practice_id)
            yield 2.0
        return self.do_task(check_opponent_task)

    def try_practice(self):
        def try_practice_task(task):
            self.click(240, 410)
            yield 1.0
        return self.do_task(try_practice_task)

    def select_fleet(self, fleet_id):
        def select_fleet_task(task):
            self.click(165 + 30 * fleet_id, 90)
            yield 1.0
        return self.do_task(select_fleet_task)

    def confirm_practice(self):
        def confirm_practice_task(task):
            self.click(470, 430)
            yield 3.0
            self.update_screen_id(screens.PRACTICE)
        return self.do_task(confirm_practice_task)

    def cancel(self):
        def cancel_task(task):
            self.click(750, 30)
            yield 1.0
        return self.do_task(cancel_task)


class PortMissionScreen(PortScreen):

    def change_screen(self, screen_id):
        def change_screen_task(task):
            if screen_id == screens.PORT_MISSION:
                yield 0.0
                return
            yield super(PortMissionScreen, self).change_screen(screen_id)
            # TODO: This is a boilerplate. Consider to extract as a method.
            if self.screen_id == screen_id:
                return
            else:
                self.raise_impossible_transition(screen_id)
        return self.do_task(change_screen_task)

    def select_maparea(self, maparea_id):
        def select_maparea_task(task):
            # Limited time map areas.
            if maparea_id >= kcsapi.MapInfo.MAPAREA_2014_SPRING:
                self.click(520, 435)
            else:
                self.click(78 + 59 * maparea_id, 435)
            yield 2.0
        return self.do_task(select_maparea_task)

    def select_mission(self, mission_index):
        def select_mission_task(task):
            self.click(300, 175 + 30 * mission_index)
            yield 2.0
        return self.do_task(select_mission_task)

    def confirm(self):
        def confirm_task(task):
            self.click(680, 450)
            yield 2.0
        return self.do_task(confirm_task)

    def select_fleet(self, fleet_id):
        def select_fleet_task(task):
            self.click(335 + 30 * fleet_id, 120)
            yield 2.0
        return self.do_task(select_fleet_task)

    def finalize(self):
        def finalize_task(task):
            self.click(630, 450)
            yield 5.0
        return self.do_task(finalize_task)


class PortOperationsScreen(PortScreen):

    def change_screen(self, screen_id):
        screen_map = {
            screens.PORT_ORGANIZING: self.click_organizing_button,
            screens.PORT_LOGISTICS: self.click_logistics_button,
            screens.PORT_REBUILDING: self.click_rebuilding_button,
            screens.PORT_REPAIR: self.click_repair_button,
            screens.PORT_SHIPYARD: self.click_shipyard_button,
        }

        def change_screen_task(task):
            if self.screen_id == screen_id:
                yield 0.0
                return
            if screen_id == screens.PORT_MAIN:
                self.click_port_button()
                yield self.wait_transition(screens.PORT_MAIN)
                return
            if screen_id in screen_map:
                screen_map[screen_id]()
                yield 2.0
                self.update_screen_id(screen_id)
                return
            yield super(PortOperationsScreen, self).change_screen(screen_id)
            if self.screen_id == screen_id:
                return
            else:
                self.raise_impossible_transition(screen_id)
        return self.do_task(change_screen_task)

    def click_organizing_button(self):
        self.click(20, 155)

    def click_logistics_button(self):
        self.click(20, 210)

    def click_rebuilding_button(self):
        self.click(20, 265)

    def click_repair_button(self):
        self.click(20, 320)

    def click_shipyard_button(self):
        self.click(20, 375)


class PortOrganizingScreen(PortOperationsScreen):

    def change_screen(self, screen_id):
        def change_screen_task(task):
            if screen_id == screens.PORT_ORGANIZING:
                yield 0.0
                return
            yield super(PortOrganizingScreen, self).change_screen(screen_id)
            if self.screen_id == screen_id:
                return
            else:
                self.raise_impossible_transition(screen_id)
        self.assert_screen(screens.PORT_ORGANIZING)
        return self.do_task(change_screen_task)

    def select_fleet(self, fleet_id):
        def select_fleet_task(task):
            self.click(105 + 30 * fleet_id, 115)
            yield 1.0
        return self.do_task(select_fleet_task)

    def detach_all_ships(self):
        def detach_all_ships_task(task):
            self.click(420, 120)
            yield 2.0
        return self.do_task(detach_all_ships_task)

    def change_member(self, index):
        def change_member_task(task):
            self.click(410 + 340 * (index % 2), 220 + 110 * (index / 2))
            yield 1.0
        return self.do_task(change_member_task)

    def select_page(self, page, max_page):
        def select_page_task(task):
            if page == max_page:
                self.click_page_last()
                yield 0.5
                return
            self.click_page_reset()
            yield 0.5
            if page <= 5:
                self.click_page(page - 1)
                yield 0.5
                return
            current_page = 1
            while page - current_page >= 5:
                self.click_page_skip_5()
                current_page += 5
                yield 0.5
            while page - current_page >= 2:
                self.click_page_next_2()
                current_page += 2
                yield 0.5
            while page > current_page:
                self.click_page_next()
                current_page += 1
                yield 0.5
        return self.do_task(select_page_task)

    def select_ship(self, index):
        def select_ship_task(task):
            self.click(500, 168 + 28 * index)
            yield 1.0
        return self.do_task(select_ship_task)

    def toggle_lock(self, index):
        def toggle_lock_task(task):
            self.click(760, 168 + 28 * index)
            yield 2.0
        return self.do_task(toggle_lock_task)

    def confirm(self):
        def confirm_task(task):
            self.click(695, 445)
            # TODO: Maybe best to detect change KCSAPI.
            yield 2.0
        return self.do_task(confirm_task)

    def unfocus_ship_selection(self):
        def unfocus_ship_selection_task(task):
            self.click(200, 160)
            yield 2.0
        return self.do_task(unfocus_ship_selection_task)

    def dissolve_combined_fleet(self):
        def dissolve_combined_fleet_task(task):
            self.click(150, 105)
            yield 2.0
        return self.do_task(dissolve_combined_fleet_task)

    def form_combined_fleet(self, fleet_type):
        def form_combined_fleet_task(task):
            self.click_hold(165, 120)
            yield 0.5
            # This subtle mouse move is required to be recognized as the drag
            # and drop from the Kancolle player.
            self.move_mouse(155, 120)
            yield 0.5
            self.move_mouse(145, 120)
            yield 0.5
            self.click_release(135, 120)
            yield 2.0
            self.click(300 + 200 * fleet_type, 240)
            yield 2.0
            self.click(400, 420)
            yield 2.0
        return self.do_task(form_combined_fleet_task)

    def click_page(self, position):
        # position ranges from 0 to 4.
        self.click(514 + 32 * position, 450)

    def click_page_reset(self):
        self.click(435, 450)

    def click_page_last(self):
        self.click(715, 450)

    def click_page_next(self):
        self.click_page(3)

    def click_page_next_2(self):
        self.click_page(4)

    def click_page_skip_5(self):
        self.click(680, 450)


class PortLogisticsScreen(PortOperationsScreen):

    def change_screen(self, screen_id):
        def change_screen_task(task):
            if screen_id == screens.PORT_LOGISTICS:
                yield 0.0
                return
            yield super(PortLogisticsScreen, self).change_screen(screen_id)
            if self.screen_id == screen_id:
                return
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
            yield 3.0
        return self.do_task(charge_both_task)


class PortRebuildingScreen(PortOperationsScreen):

    def change_screen(self, screen_id):
        def change_screen_task(task):
            if screen_id == screens.PORT_REBUILDING:
                yield 0.0
                return
            yield super(PortRebuildingScreen, self).change_screen(screen_id)
            if self.screen_id == screen_id:
                return
            else:
                self.raise_impossible_transition(screen_id)
        self.assert_screen(screens.PORT_REBUILDING)
        return self.do_task(change_screen_task)

    def select_fleet(self, fleet_id):
        def select_fleet_task(task):
            self.click(120 + 30 * fleet_id, 115)
            yield 1.0
        return self.do_task(select_fleet_task)

    def select_fleet_ship(self, ship_index):
        def select_fleet_ship_task(task):
            self.click(210, 165 + 55 * ship_index)
            yield 1.0
        return self.do_task(select_fleet_ship_task)

    def select_ship_list(self):
        def select_ship_list_task(task):
            self.click(270, 115)
            yield 1.0
        return self.do_task(select_ship_list_task)

    def try_rebuilding(self):
        def try_rebuilding_task(task):
            self.click(615, 440)
            yield 2.0
        return self.do_task(try_rebuilding_task)

    def select_slot(self, slot_index):
        def select_slot_task(task):
            self.click(570, 140 + 60 * slot_index)
            yield 1.0
        return self.do_task(select_slot_task)

    def finalize_rebuilding(self):
        def finalize_rebuilding_task(task):
            self.click(710, 440)
            yield 1.0
        return self.do_task(finalize_rebuilding_task)

    def confirm_rebuilding(self):
        def confirm_rebuilding_task(task):
            self.click(490, 410)
            yield self.wait_transition(screens.PORT_REBUILDING_REBUILDRESULT)
        return self.do_task(confirm_rebuilding_task)

    def check_rebuilding_result(self):
        def check_rebuilding_result_task(task):
            yield 6.0
            self.click_somewhere()
            yield 2.0
        return self.do_task(check_rebuilding_result_task)

    def try_remodeling(self):
        def try_remodeling_task(task):
            self.click(735, 440)
            yield 2.0
        return self.do_task(try_remodeling_task)

    finalize_remodeling = finalize_rebuilding

    def confirm_remodeling(self):
        def confirm_remodeling_task(task):
            self.click(490, 410)
            yield self.wait_transition(screens.PORT_REBUILDING_REMODELRESULT)
        return self.do_task(confirm_remodeling_task)

    def check_remodeling_result(self):
        def check_remodeling_result_task(task):
            yield 6.0
            self.click_somewhere()
            self.update_screen_id(screens.PORT_REBUILDING)
            yield 2.0
        return self.do_task(check_remodeling_result_task)

    def cancel(self):
        def cancel_task(task):
            self.click(545, 445)
            self.update_screen_id(screens.PORT_REBUILDING)
            yield 2.0
        return self.do_task(cancel_task)

    def select_page(self, page):
        def select_page_task(task):
            if page <= 3:
                self.click_page(page - 1)
                yield 0.5
                return
            current_page = 1
            while page - current_page >= 3:
                self.click_page_skip_3()
                current_page += 3
                yield 0.5
            while page > current_page:
                self.click_page_next()
                current_page += 1
                yield 0.5
        return self.do_task(select_page_task)

    def select_ship(self, index):
        def select_ship_task(task):
            self.click(210, 150 + 29 * index)
            yield 1.0
        return self.do_task(select_ship_task)

    def click_page(self, position):
        # position ranges from 0 to 2.
        self.click(180 + 35 * position, 450)

    def click_page_next(self):
        self.click_page(2)

    def click_page_skip_3(self):
        self.click(275, 450)

    def select_material_page(self, page, max_page):
        def select_material_page_task(task):
            if page == max_page:
                self.click_material_page_last()
                yield 0.5
                return
            self.click_material_page_reset()
            yield 0.5
            if page <= 5:
                self.click_material_page(page - 1)
                yield 0.5
                return
            current_page = 1
            while page - current_page >= 5:
                self.click_material_page_skip_5()
                current_page += 5
                yield 0.5
            while page - current_page >= 2:
                self.click_material_page_next_2()
                current_page += 2
                yield 0.5
            while page > current_page:
                self.click_material_page_next()
                current_page += 1
                yield 0.5
        return self.do_task(select_material_page_task)

    def select_material_ship(self, index):
        def select_material_ship_task(task):
            self.click(600, 140 + 30 * index)
            yield 2.0
        return self.do_task(select_material_ship_task)

    def click_material_page(self, position):
        # position ranges from 0 to 4.
        self.click(558 + 32 * position, 450)

    def click_material_page_reset(self):
        self.click(480, 450)

    def click_material_page_last(self):
        self.click(760, 450)

    def click_material_page_next(self):
        self.click_material_page(3)

    def click_material_page_next_2(self):
        self.click_material_page(4)

    def click_material_page_skip_5(self):
        self.click(725, 450)

    def clear_all_item_slots(self, num_slots):
        def clear_all_item_slots_task(task):
            self.click(327, 168 + 32 * num_slots)
            yield 2.0
        if num_slots == 1:
            return self.clear_item_slot(0)
        return self.do_task(clear_all_item_slots_task)

    def clear_item_slot(self, slot_index):
        def clear_item_slot_task(task):
            self.click(550, 177 + 32 * slot_index)
            yield 2.0
        return self.do_task(clear_item_slot_task)

    def select_item_slot(self, slot_index):
        def select_item_slot_task(task):
            self.click(450, 177 + 32 * slot_index)
            yield 1.0
        return self.do_task(select_item_slot_task)

    def select_item_page(self, page, max_page):
        def select_item_page_task(task):
            if page == max_page:
                self.click_item_page_last()
                yield 0.5
                return
            self.click_item_page_reset()
            yield 0.5
            if page <= 5:
                self.click_item_page(page - 1)
                yield 0.5
                return
            current_page = 1
            while page - current_page >= 5:
                self.click_item_page_skip_5()
                current_page += 5
                yield 0.5
            while page - current_page >= 2:
                self.click_item_page_next_2()
                current_page += 2
                yield 0.5
            while page > current_page:
                self.click_item_page_next()
                current_page += 1
                yield 0.5
        return self.do_task(select_item_page_task)

    def select_item(self, index):
        def select_item_task(task):
            self.click(450, 145 + 30 * index)
            yield 1.0
        return self.do_task(select_item_task)

    def toggle_item_lock(self, index):
        def toggle_item_lock_task(task):
            self.click(785, 145 + 30 * index)
            yield 2.0
        return self.do_task(toggle_item_lock_task)

    def confirm_item_replacement(self):
        def confirm_item_replacement_task(task):
            self.click(700, 440)
            # TODO: Maybe best to detect ship3 KCSAPI.
            yield 2.0
        return self.do_task(confirm_item_replacement_task)

    def unfocus_selection(self):
        def unfocus_selection_task(task):
            self.click(120, 120)
            yield 2.0
        return self.do_task(unfocus_selection_task)

    def click_item_page(self, position):
        # position ranges from 0 to 4.
        self.click(492 + 32 * position, 450)

    def click_item_page_reset(self):
        self.click(410, 450)

    def click_item_page_last(self):
        self.click(690, 450)

    def click_item_page_next(self):
        self.click_item_page(3)

    def click_item_page_next_2(self):
        self.click_item_page(4)

    def click_item_page_skip_5(self):
        self.click(660, 450)


class PortRepairScreen(PortOperationsScreen):

    def change_screen(self, screen_id):
        def change_screen_task(task):
            if screen_id == screens.PORT_REPAIR:
                yield 0.0
                return
            yield super(PortRepairScreen, self).change_screen(screen_id)
            if self.screen_id == screen_id:
                return
            else:
                self.raise_impossible_transition(screen_id)
        self.assert_screen(screens.PORT_REPAIR)
        return self.do_task(change_screen_task)

    def select_slot(self, slot_id):
        def select_slot_task(task):
            self.click(255, 90 + 80 * slot_id)
            yield 2.0
        return self.do_task(select_slot_task)

    def select_page(self, page):
        def select_page_task(task):
            self.click_page_reset()
            yield 0.5
            if page <= 5:
                self.click_page(page - 1)
                yield 0.5
                return
            current_page = 1
            while page - current_page >= 5:
                self.click_page_skip_5()
                current_page += 5
                yield 0.5
            while page - current_page >= 2:
                self.click_page_next_2()
                current_page += 2
                yield 0.5
            while page > current_page:
                self.click_page_next()
                current_page += 1
                yield 0.5
        return self.do_task(select_page_task)

    def select_ship(self, index):
        def select_ship_task(task):
            self.click(500, 140 + 31 * index)
            yield 1.0
        return self.do_task(select_ship_task)

    def try_repair(self):
        def try_repair_task(task):
            self.click(685, 440)
            yield 2.0
        return self.do_task(try_repair_task)

    def confirm_repair(self):
        def confirm_repair_task(task):
            self.click(505, 400)
            # TODO: This is better to wait nyukyo KCSAPI.
            yield 3.0
        return self.do_task(confirm_repair_task)

    def boost_repair(self, slot_index):
        def boost_repair_task(task):
            self.click(755, 160 + 80 * slot_index)
            yield 2.0
        return self.do_task(boost_repair_task)

    def confirm_boost(self):
        def confirm_boost_task(task):
            self.click(505, 405)
            # Oftentimes AutoRepairShips will schedule itself right after
            # boosting repair. This wait ensures it will not overlap.
            yield 12.0
        return self.do_task(confirm_boost_task)

    def click_page(self, position):
        # position ranges from 0 to 4.
        self.click(516 + 32 * position, 460)

    def click_page_reset(self):
        self.click(435, 460)

    def click_page_next(self):
        self.click_page(3)

    def click_page_next_2(self):
        self.click_page(4)

    def click_page_skip_5(self):
        self.click(680, 460)


class PortShipyardScreen(PortOperationsScreen):

    def change_screen(self, screen_id):
        def change_screen_task(task):
            if screen_id == screens.PORT_SHIPYARD:
                yield 0.0
                return
            yield super(PortShipyardScreen, self).change_screen(screen_id)
            if self.screen_id == screen_id:
                return
            else:
                self.raise_impossible_transition(screen_id)
        self.assert_screen(screens.PORT_SHIPYARD)
        return self.do_task(change_screen_task)

    def select_slot(self, slot_id):
        def select_slot_task(task):
            self.click(620, 180 + 80 * slot_id)
            yield 2.0
        return self.do_task(select_slot_task)

    def try_grand_building(self):
        def try_grand_building_task(task):
            self.click(380, 445)
            yield 2.0
            self.click(340, 355)
            yield 2.0
        return self.do_task(try_grand_building_task)

    def set_material(self, material):
        def set_material_task(task):
            if material == 1:
                return
            elif material == 20:
                self.click(682, 400)
                yield 1.0
            elif material == 100:
                self.click(718, 400)
                yield 1.0
        return self.do_task(set_material_task)

    def set_resource(self, grand, fuel, ammo, steel, bauxite):
        initial_fuel = 1500 if grand else 30
        initial_ammo = 1500 if grand else 30
        initial_steel = 2000 if grand else 30
        initial_bauxite = 1000 if grand else 30

        def set_resource_task(task):
            yield self.set_resource_amount(grand, fuel, initial_fuel, 0, 0)
            yield self.set_resource_amount(grand, ammo, initial_ammo, 1, 0)
            yield self.set_resource_amount(grand, steel, initial_steel, 0, 1)
            yield self.set_resource_amount(
                grand, bauxite, initial_bauxite, 1, 1)
        return self.do_task(set_resource_task)

    def set_resource_amount(self, grand, amount, initial_amount, row, col):
        def set_resource_amount_task(task):
            base_x = 308 + 228 * col
            base_y = 119 + 130 * row
            x_skip_offset = 5 if grand else 0
            tick = 10 if grand else 1
            small_skip = 100 if grand else 10
            big_skip = 1000 if grand else 100
            current_amount = initial_amount
            while amount - current_amount >= big_skip:
                self.click_big_skip(base_x + x_skip_offset, base_y)
                current_amount += big_skip
                yield 0.5
            while amount - current_amount >= small_skip:
                self.click_small_skip(base_x + x_skip_offset, base_y)
                current_amount += small_skip
                yield 0.5
            while amount - current_amount >= tick:
                self.click_tick(base_x, base_y)
                current_amount += tick
                yield 0.5
        return self.do_task(set_resource_amount_task)

    def confirm_building(self):
        def confirm_building_task(task):
            self.click(710, 445)
            yield 2.0
        return self.do_task(confirm_building_task)

    def boost_build(self, slot_index):
        def boost_build_task(task):
            self.click(745, 185 + 80 * slot_index)
            yield 2.0
        return self.do_task(boost_build_task)

    def confirm_boost(self):
        def confirm_boost_task(task):
            self.click(485, 385)
            yield 10.0
        return self.do_task(confirm_boost_task)

    def check_ship(self):
        def check_ship_task(task):
            yield 10.0
            self.click_somewhere()
            yield self.transition_to(screens.PORT_SHIPYARD)
        return self.do_task(check_ship_task)

    def try_equipment_development(self):
        def try_equipment_development_task(task):
            self.click(230, 340)
            yield 1.0
        return self.do_task(try_equipment_development_task)

    def set_development_resource(self, fuel, ammo, steel, bauxite):
        def set_development_resource_task(task):
            yield self.set_resource_amount(False, fuel, 10, 0, 0)
            yield self.set_resource_amount(False, ammo, 10, 1, 0)
            yield self.set_resource_amount(False, steel, 10, 0, 1)
            yield self.set_resource_amount(False, bauxite, 10, 1, 1)
        return self.do_task(set_development_resource_task)

    def confirm_development(self):
        def confirm_development_task(task):
            self.click(710, 445)
            yield 2.0
        return self.do_task(confirm_development_task)

    def check_equipment(self):
        def check_equipment_task(task):
            yield 10.0
            self.click_somewhere()
            yield self.transition_to(screens.PORT_SHIPYARD)
        return self.do_task(check_equipment_task)

    def try_dissolution(self):
        def try_dissolution_task(task):
            self.click(235, 260)
            yield 2.0
        return self.do_task(try_dissolution_task)

    def select_page(self, page, max_page):
        def select_page_task(task):
            if page == max_page:
                self.click_page_last()
                yield 0.5
                return
            self.click_page_reset()
            yield 0.5
            if page <= 5:
                self.click_page(page - 1)
                yield 0.5
                return
            current_page = 1
            while page - current_page >= 5:
                self.click_page_skip_5()
                current_page += 5
                yield 0.5
            while page - current_page >= 2:
                self.click_page_next_2()
                current_page += 2
                yield 0.5
            while page > current_page:
                self.click_page_next()
                current_page += 1
                yield 0.5
        return self.do_task(select_page_task)

    def select_ship(self, index):
        def select_ship_task(task):
            self.click(300, 140 + 31 * index)
            yield 1.0
        return self.do_task(select_ship_task)

    def confirm_dissolution(self):
        def confirm_dissolution_task(task):
            self.click(700, 440)
            yield 5.0
        return self.do_task(confirm_dissolution_task)

    def unfocus_selection(self):
        def unfocus_selection_task(task):
            self.click(120, 120)
            yield 2.0
        return self.do_task(unfocus_selection_task)

    def click_big_skip(self, base_x, base_y):
        self.click(base_x + 184, base_y + 46)

    def click_small_skip(self, base_x, base_y):
        self.click(base_x + 184, base_y + 20)

    def click_tick(self, base_x, base_y):
        self.click(base_x + 56, base_y + 38)

    def click_page(self, position):
        # position ranges from 0 to 4.
        self.click(299 + 32 * position, 450)

    def click_page_reset(self):
        self.click(220, 450)

    def click_page_last(self):
        self.click(500, 450)

    def click_page_next(self):
        self.click_page(3)

    def click_page_next_2(self):
        self.click_page(4)

    def click_page_skip_5(self):
        self.click(465, 450)

    def try_item_dissolution(self):
        def try_item_dissolution_task(task):
            self.click(220, 415)
            yield 2.0
        return self.do_task(try_item_dissolution_task)

    select_item_page = select_page

    def select_item(self, index):
        def select_item_task(task):
            self.click(300, 140 + 31 * index)
            yield 1.0
        return self.do_task(select_item_task)

    confirm_item_dissolution = confirm_dissolution


class EngageScreen(Screen):

    def select_formation(self, formation):
        def select_formation_task(task):
            click_positions = {
                0: (450, 185),   # FORMATION_SINGLE_LINE
                1: (580, 185),   # FORMATION_DOUBLE_LINES
                2: (710, 185),   # FORMATION_CIRCLE
                3: (520, 345),   # FORMATION_LADDER
                4: (650, 345),   # FORMATION_HORIZONTAL_LINE
                11: (500, 175),  # FORMATION_COMBINED_ANTI_SUBMARINE
                12: (665, 175),  # FORMATION_COMBINED_LOOKOUT
                13: (500, 315),  # FORMATION_COMBINED_CIRCLE
                14: (665, 315),  # FORMATION_COMBINED_COMBAT
            }
            self.click(*click_positions[formation])
            yield 1.0
        return self.do_task(select_formation_task)

    def avoid_night_combat(self):
        def avoid_night_combat_task(task):
            self.click(290, 245)
            yield 2.0
        return self.do_task(avoid_night_combat_task)

    def engage_night_combat(self):
        def engage_night_combat_task(task):
            self.click(505, 245)
            yield 2.0
        return self.do_task(engage_night_combat_task)

    def dismiss_result_overview(self):
        def dismiss_result_overview_task(task):
            yield 8.0
            self.click_somewhere()
            yield 5.0
        return self.do_task(dismiss_result_overview_task)


class ExpeditionScreen(EngageScreen):

    def roll_compass(self):
        def roll_compass_task(task):
            yield 2.0
            self.click_somewhere()
            yield 4.0
        return self.do_task(roll_compass_task)

    def select_next_location(self, click_position):
        def select_next_location_task(task):
            yield 2.0
            self.click(*click_position)
            # Do not wait, the next KCSAPI will come soon.
        return self.do_task(select_next_location_task)

    def dismiss_boss_conversation(self):
        def dismiss_boss_conversation_task(task):
            yield 7.0
            self.click_somewhere()
            yield 2.0
        return self.do_task(dismiss_boss_conversation_task)

    def proceed_terminal_screen(self):
        def proceed_terminal_screen_task(task):
            yield 7.0
            self.click_somewhere()
            yield self.wait_transition(screens.PORT_MAIN)
        return self.do_task(proceed_terminal_screen_task)

    def dismiss_result_details(self):
        def dismiss_result_details_task(task):
            self.click_somewhere()
            yield 2.0
        return self.do_task(dismiss_result_details_task)

    def dismiss_new_ship(self):
        def dismiss_new_ship_task(task):
            yield 7.0
            self.click(750, 430)
            yield 3.0
        return self.do_task(dismiss_new_ship_task)

    dismiss_new_item = dismiss_new_ship

    def dismiss_first_clear_screen(self):
        def dismiss_first_clear_screen_task(task):
            yield 15.0
            self.click(750, 430)
            yield 5.0
        return self.do_task(dismiss_first_clear_screen_task)

    def go_for_next_battle(self):
        def go_for_next_battle_task(task):
            self.click(290, 245)
            yield 2.0
        return self.do_task(go_for_next_battle_task)

    def forcedly_drop_out(self):
        def forcedly_drop_out_task(task):
            yield 5.0
            self.click_somewhere()
            yield self.wait_transition(screens.PORT_MAIN)
        return self.do_task(forcedly_drop_out_task)

    def drop_out(self):
        def drop_out_task(task):
            self.click(505, 245)
            yield self.wait_transition(screens.PORT_MAIN)
        return self.do_task(drop_out_task)


class PracticeScreen(EngageScreen):

    def dismiss_result_details(self):
        def dismiss_result_details_task(task):
            self.click_somewhere()
            yield self.wait_transition(screens.PORT_MAIN)
        return self.do_task(dismiss_result_details_task)


class MissionResultScreen(Screen):

    def proceed_mission_result_screen(self):
        def proceed_mission_result_screen_task(task):
            self.assert_screen(screens.MISSION_RESULT)
            self._logger.debug('This is mission result screen.')
            yield 5.0
            self.click_somewhere()
            yield 3.0
            self.click_somewhere()
            self._logger.debug('And now we are at the port main.')
            yield self.transition_to(screens.PORT_MAIN)
        return self.do_task(proceed_mission_result_screen_task)

    def click_record_button(self):
        def click_record_button_task(task):
            self.click(165, 50)
            yield 2.0
        return self.do_task(click_record_button_task)
