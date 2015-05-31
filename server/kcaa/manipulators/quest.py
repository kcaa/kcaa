#!/usr/bin/env python

import logging

import base
from kcaa import screens


logger = logging.getLogger('kcaa.manipulators.quest')


class CheckQuests(base.Manipulator):

    def run(self):
        quest_list = self.objects['QuestList']
        yield self.screen.change_screen(screens.PORT_QUESTLIST)
        max_page = quest_list.max_page
        yield self.screen.select_page(1, max_page)
        for _ in xrange(max_page - 1):
            yield self.screen.click_next_page_button()
