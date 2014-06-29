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
