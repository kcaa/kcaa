#!/usr/bin/env python

from kcaa import task


class Manipulator(task.Task):

    def __init__(self, manager, **kwargs):
        # Be sure to store required fields before calling super(), because
        # super() will call run() inside it.
        self.objects = manager.objects
        self.manager = manager
        self._screen_manager = manager.screen_manager
        super(Manipulator, self).__init__(**kwargs)

    @property
    def screen_id(self):
        return self._screen_manager.current_screen.screen_id

    @property
    def screen(self):
        return self._screen_manager.current_screen

    # TODO: Methods for do_task (run soon as a blocking task), add_manipulator
    # (run later), and run right after this manipulator
