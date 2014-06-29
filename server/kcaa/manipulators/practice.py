#!/usr/bin/env python

import logging

import base
from kcaa import screens
from kcaa.kcsapi import practice


logger = logging.getLogger('kcaa.manipulators.practice')


class CheckPracticeOpponents(base.Manipulator):

    def run(self):
        logger.info('Checking practice opponents')
        yield self.screen.change_screen(screens.PORT_PRACTICE)
        practice_list = self.objects.get('PracticeList')
        if not practice_list:
            logger.info('No practice list was found. Giving up.')
            return
        for practice_ in practice_list.practices:
            if practice_.result != practice.Practice.RESULT_NEW:
                continue
            yield self.screen.check_opponent(practice_.id)
            yield self.screen.cancel(practice_.id)


class GoOnPractice(base.Manipulator):

    def run(self, practice_id):
        practice_id = int(practice_id)
        # TODO: Support other fleets.
        logger.info('Making the fleet 1 go on the practice {}'.format(
            practice_id))
        yield self.screen.change_screen(screens.PORT_PRACTICE)
        practice_list = self.objects.get('PracticeList')
        if not practice_list:
            logger.info('No practice list was found. Giving up.')
            return
        practice_ = practice_list.practices[practice_id - 1]
        if practice_.result != practice.Practice.RESULT_NEW:
            logger.error('Practice {} is already done.'.format(practice_id))
            return
        yield self.screen.check_opponent(practice_.id)
        yield self.screen.try_practice()
        yield self.screen.confirm_practice()
        # TODO: Select the formation and proceed.
