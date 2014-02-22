#!/usr/bin/env python

import base64
import json
import logging
import re
import urlparse

import kcsapi


KCSAPI_PATH_REGEX = re.compile(r'/kcsapi(?P<api_name>/.*)')
KCSAPI_PREFIX = 'svdata='


class KCSAPIHandler(object):

    def __init__(self, har_manager):
        self._logger = logging.getLogger('kcaa.kcsapi_util')
        self.har_manager = har_manager
        self.debug = True
        self.objects = {}
        self.define_handlers()

    def define_handlers(self):
        """Define KCSAPI handlers.

        The reason to define handlers here, not in a module level, is to
        refresh the handler class objects to reflect what's in source files
        under kcsapi/ directory. Note that this list itself is not reloaded;
        if you want to add a handler or change something, you still need to
        restart the server. (Or you can change the controller code to reload
        this module as well, if you prefer. But reloading module is tricky, so
        I'd recommend you not to abuse too much.)
        """
        self.kcsapi_handlers = {
            '/api_get_member/questlist': [kcsapi.questlist.QuestList],
        }

    def reload_handlers(self):
        """Reload KCSAPI handler modules to reflect possible bug fixes in
        source files."""
        reload(kcsapi)
        kcsapi.reload_modules()
        # As all models are reloaded, there is no compatibility between old
        # objects and the new objects. Old ones need to be disposed.
        self.objects.clear()
        self.define_handlers()

    def get_kcsapi_responses(self, entries):
        for entry in entries:
            o = urlparse.urlparse(entry['request']['url'])
            match = KCSAPI_PATH_REGEX.match(o.path)
            if match:
                api_name = match.group('api_name')
                content = entry['response']['content']
                text = content['text']
                # Highly likely the KCSAPI response is Base64 encoded, because
                # the API server doesn't attach charset information.
                encoding = content.get('encoding')
                if encoding == 'base64':
                    text = base64.b64decode(text)
                # Skip response prefix which makes JSON parsing fail.
                if text.startswith(KCSAPI_PREFIX):
                    text = text[len(KCSAPI_PREFIX):]
                else:
                    self._logger.debug(
                        'Unexpected KCSAPI response: {}'.format(text))
                # KCSAPI response should be in UTF-8.
                response = json.loads(text, encoding='utf8')
                yield api_name, response

    def dispatch(self, api_name, response):
        try:
            handlers = self.kcsapi_handlers[api_name]
            self._logger.debug('Accessed KCSAPI: {}'.format(api_name))
        except KeyError:
            handlers = [kcsapi.model.DefaultHandler(api_name)]
            self._logger.debug('Unknown KCSAPI: {}'.format(api_name))
        for handler in handlers:
            object_type = handler.__name__
            old_obj = self.objects.get(object_type)
            if not old_obj:
                obj = handler(api_name, response, self.debug)
                self.objects[object_type] = obj
            else:
                old_obj.update(api_name, response)
                obj = old_obj
            yield obj

    def get_updated_objects(self):
        entries = self.har_manager.get_updated_entries()
        if not entries:
            return
        for api_name, response in self.get_kcsapi_responses(entries):
            for obj in self.dispatch(api_name, response):
                yield obj
