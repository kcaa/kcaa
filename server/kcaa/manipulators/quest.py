#!/usr/bin/env python

import datetime
import logging

import base
from kcaa import screens


logger = logging.getLogger('kcaa.manipulators.quest')


class CheckQuests(base.Manipulator):

    def run(self):
        yield self.screen.change_screen(screens.PORT_QUESTLIST)
        quest_list = self.objects['QuestList']
        max_page = quest_list.max_page
        yield self.screen.select_page(1, max_page)
        for _ in xrange(max_page - 1):
            yield self.screen.click_next_page_button()


# TODO: Add a new subclass of AutoManipulator, named ScheduledManipulator. The
# most of infrastructural code of this can be shared with
# AutoCheckPracticeOpponents and probably QuestList checker.
class AutoCheckQuests(base.AutoManipulator):

    schedules = [datetime.time(5, 5)]

    next_update = None

    @classmethod
    def precondition(cls, owner):
        return screens.in_category(owner.screen_id, screens.PORT)

    @classmethod
    def can_trigger(cls, owner):
        now = datetime.datetime.now()
        initial_run = cls.next_update is None
        if not initial_run and now < cls.next_update:
            return
        t = now.time()
        for next_schedule in cls.schedules:
            if t < next_schedule:
                cls.next_update = datetime.datetime.combine(
                    now.date(), next_schedule)
                break
        else:
            cls.next_update = datetime.datetime.combine(
                now.date() + datetime.timedelta(days=1), cls.schedules[0])
        logger.debug(
            'Next quest update is scheduled at {}'.format(cls.next_update))
        if not initial_run or 'QuestList' not in owner.objects:
            return {}

    def run(self):
        yield self.do_manipulator(CheckQuests)
