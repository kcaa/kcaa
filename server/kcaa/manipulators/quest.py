#!/usr/bin/env python

import datetime
import logging

import base
from kcaa import kcsapi
from kcaa import screens


logger = logging.getLogger('kcaa.manipulators.quest')


class CheckQuests(base.Manipulator):

    @staticmethod
    def get_first_completed_quest_index(quests):
        for index, quest in enumerate(quests):
            if quest.state == kcsapi.Quest.STATE_COMPLETE:
                return index
        return -1

    def run(self):
        yield self.screen.change_screen(screens.PORT_QUESTLIST)
        quest_list = self.objects['QuestList']
        while True:
            max_page = quest_list.max_page
            yield self.screen.select_page(1, max_page)
            index = CheckQuests.get_first_completed_quest_index(
                quest_list.quests[0:min(5, len(quest_list.quests))])
            if index >= 0:
                yield self.screen.complete_quest(index)
                # There should not be a chance to consume all available
                # quests... in almost all cases, probably.
                continue
            to_finish = True
            page = 1
            for _ in xrange(max_page - 1):
                yield self.screen.click_next_page_button()
                page += 1
                offset = 5 * (page - 1)
                max_offset = min(offset + 5, len(quest_list.quests))
                index = CheckQuests.get_first_completed_quest_index(
                    quest_list.quests[offset:max_offset])
                if index >= 0:
                    yield self.screen.complete_quest(index)
                    # There is a chance to consume the last quest in the last
                    # page. In such a case the second quest list update will
                    # transition the client screen to the new last page.
                    # Wait for it to happen.
                    if page == max_page:
                        yield 2.0
                    logger.debug(
                        'Found a completed quest. Restart the traversal to '
                        'refresh the quest list.')
                    to_finish = False
                    break
            if to_finish:
                break


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


class UndertakeQuest(base.Manipulator):

    @staticmethod
    def find_quest(quest_id, quests):
        for index, quest in enumerate(quests):
            if quest.id == quest_id:
                return index
        return -1

    def run(self, quest_id, undertaken):
        quest_id = int(quest_id)
        undertaken = undertaken is False or undertaken != 'false'
        # Check if there is a matching quest and already undertaken.
        quest_list = self.objects.get('QuestList')
        if quest_list:
            quest = quest_list.get_quest(quest_id)
            if quest:
                quest_active = quest.state != kcsapi.Quest.STATE_INACTIVE
                if quest_active == undertaken:
                    logger.debug(
                        'Found a matching quest and the state is already '
                        'fulfilled.')
                    return
        # Unlike other objects, there is no guarantee that the QuestList is
        # complete. Traverse it and find on the fly.
        # If no user interacts with the quest screen, it's possible to use
        # select_page() to efficiently spot the quest in question.
        logger.info('{} the quest {}.'.format(
            'Undertaking' if undertaken else 'Cancelling', quest_id))
        yield self.screen.change_screen(screens.PORT_QUESTLIST)
        quest_list = self.objects['QuestList']
        max_page = quest_list.max_page
        yield self.screen.select_page(1, max_page)
        index = UndertakeQuest.find_quest(
            quest_id, quest_list.quests[0:min(5, len(quest_list.quests))])
        if index >= 0:
            yield self.screen.toggle_quest(index)
            return
        for _ in xrange(max_page - 1):
            yield self.screen.click_next_page_button()
            offset = 5 * (self.screen.current_page - 1)
            max_offset = min(offset + 5, len(quest_list.quests))
            index = UndertakeQuest.find_quest(
                quest_id, quest_list.quests[offset:max_offset])
            if index >= 0:
                yield self.screen.toggle_quest(index)
                return
        raise Exception('No quest found with ID {}'.format(quest_id))
