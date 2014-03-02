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

    def wait_transition(self, screen_id, timeout=5.0, raise_on_timeout=True,
                        buffer_delay=1.0):
        """Wait until the screen transition."""
        def wait_transition_task(task):
            while self.screen_id != screen_id:
                if task.time > timeout:
                    if raise_on_timeout:
                        raise ValueError(
                            'Cannot transition to screen {}'.format(screen_id))
                    return
                yield task.unit
            yield buffer_delay
        return self.do_task(wait_transition_task)

    def change_screen(self, screen_id):
        """Change the screen."""
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

    def change_screen(self, screen_id):
        # If the current screen is unknown, go first to the port main screen,
        # and then move to the target screen.
        def change_screen_task(task):
            self.click(50, 50)  # Possibly click the rotating 'Port' button
            yield 2.0
            self.click(60, 450)  # Possibly click the 'Back' button
            yield self.wait_transition(screens.PORT)
            self.update_screen_id(screens.PORT_MAIN)
            yield task.unit
            yield self.manager.current_screen.change_screen(screen_id)
        self.assert_screen_category(screens.PORT)
        return self.do_task(change_screen_task)


class PortMainScreen(PortScreen):

    def change_screen(self, screen_id):
        def change_screen_task(task):
            print 'PortMainScreen', screen_id
            yield 0.0
        self.assert_screen(screens.PORT_MAIN)
        return self.do_task(change_screen_task)
