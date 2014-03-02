#!/usr/bin/env python

from kcaa import screens


class Screen(object):

    def __init__(self, manager):
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
            None

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

    def wait_screen_transition(self, screen_id, buffer_delay=1.0):
        """Wait until the screen transition."""
        def wait_screen_transition_task(task):
            while self.screen_id != screen_id:
                yield task.unit
            yield buffer_delay
        return self.do_task(wait_screen_transition_task)

    def change_screen(self, screen_id):
        """Change the screen."""
        raise TypeError('Cannot change screen from {} to {}'.format(
            self.screen_id, screen_id))


class StartScreen(Screen):

    def proceed(self):
        def proceed_task(task):
            self.click(620, 400)
            yield self.wait_screen_transition(screens.PORT)
        return self.do_task(proceed_task)


class PortScreen(Screen):
    pass


class PortMainScreen(PortScreen):
    pass
