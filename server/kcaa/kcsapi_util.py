#!/usr/bin/env python

import base64
import json
import logging
import re
import urlparse

import kcsapi


KCSAPI_PATH_REGEX = re.compile(r'/kcsapi(?P<api_name>/.*)')
KCSAPI_PREFIX = 'svdata='

# UTF-8 Byte Order Mark.
BOM = '\xEF\xBB\xBF'


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
        under kcsapi/ directory.
        """
        # API URLs can be classified into 4 classes:
        # - /api_get_master/FOO: Get the general definition about FOO. User
        #                        independent.
        # - /api_get_member/FOO: Get the current status about FOO. User
        #                        dependent.
        # - /api_req_FOO/BAR: Make changes on FOO by doing an action BAR.
        #                     Doesn't necessarily deliver useful information
        #                     in the response (i.e. oftentimes the request
        #                     itself is important).
        # - Others.
        self.kcsapi_handlers = {
            # Initialization, or account information
            # /api_start seems delivering information required to render
            # maparea. It's still useful for deciding what screen the client is
            # showing.
            '/api_auth_member/logincheck': [kcsapi.model.NullHandler()],
            '/api_req_member/get_incentive': [kcsapi.model.NullHandler()],
            '/api_start': [kcsapi.model.NullHandler()],
            # Encyclopedia
            '/api_get_member/book2': [kcsapi.model.NullHandler()],
            # Ships
            '/api_get_master/ship': [kcsapi.ship.ShipDefinitionList],
            '/api_get_member/ship': [kcsapi.ship.ShipList],
            '/api_get_member/ship2': [kcsapi.ship.ShipList],
            # TODO: Handle ship3.
            # Decks (Fleets)
            # Not sure what's the difference between /deck and /deck_port. They
            # share the same data structure.
            # As long as I know, /deck is used when a fleet departs for a
            # mission, and /deck_port when a user comes back to the start
            # screen (which is called a port).
            '/api_get_member/deck': [kcsapi.missionlist.MissionList],
            '/api_get_member/deck_port': [kcsapi.missionlist.MissionList],
            # Quests
            '/api_get_member/questlist': [kcsapi.questlist.QuestList],
            '/api_req_quest/start': [kcsapi.model.NullHandler()],
            '/api_req_quest/stop': [kcsapi.model.NullHandler()],
            # Missions
            '/api_get_master/mission': [kcsapi.missionlist.MissionList],
            '/api_req_mission/start': [kcsapi.model.NullHandler()],
            # Items
            #'/api_get_member/useitem': [],
            # Furnitures
            # Not interested in furniture configuration.
            '/api_get_master/furniture': [kcsapi.model.NullHandler()],
            '/api_get_member/furniture': [kcsapi.model.NullHandler()],
            # Maparea
            # Delivers only names.
            '/api_get_master/maparea': [kcsapi.model.NullHandler()],
            # Log
            # Almost useless.
            '/api_get_member/actionlog': [kcsapi.model.NullHandler()],
        }
        # Eager handlers accept all KCSAPI responses regardless of API URL.
        self.kcsapi_eager_handlers = [
            kcsapi.client.Screen,
        ]

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
                request = {param['name']: param['value'] for param in
                           entry['request']['postData']['params']}
                content = entry['response']['content']
                text = content['text']
                # Highly likely the KCSAPI response is Base64 encoded, because
                # the API server doesn't attach charset information.
                encoding = content.get('encoding')
                if encoding == 'base64':
                    text = base64.b64decode(text)
                # Remove BOM if any.
                if text.startswith(BOM):
                    text = text[len(BOM):]
                # Skip response prefix which makes JSON parsing fail.
                if text.startswith(KCSAPI_PREFIX):
                    text = text[len(KCSAPI_PREFIX):]
                else:
                    self._logger.debug(
                        'Unexpected KCSAPI response got for {}'.format(o.path))
                    self._logger.debug(
                        'Raw response: {}'.format(text))
                    self._logger.debug('First 64 bytes: {}'.format(
                        ' '.join(('{:X}'.format(ord(c))) for c in text[:64])))
                    continue
                # KCSAPI response should be in UTF-8.
                response = json.loads(text, encoding='utf8')
                yield api_name, request, response

    def dispatch(self, api_name, request, response):
        try:
            handlers = self.kcsapi_handlers[api_name]
            self._logger.debug('Accessed KCSAPI: {}'.format(api_name))
        except KeyError:
            handlers = [kcsapi.model.DefaultHandler(api_name)]
            self._logger.debug('Unknown KCSAPI:  {}'.format(api_name))
        for handler in handlers + self.kcsapi_eager_handlers:
            object_type = handler.__name__
            old_obj = self.objects.get(object_type)
            if not old_obj:
                obj = handler(api_name, request, response, self.objects,
                              self.debug)
                # Handler may return None in case there is no need to handle
                # the KCSAPI response.
                if obj:
                    self.objects[object_type] = obj
                    yield obj
            else:
                old_obj.update(api_name, request, response, self.objects)
                yield old_obj

    def get_updated_objects(self):
        entries = self.har_manager.get_updated_entries()
        if not entries:
            return
        for api_name, request, response in self.get_kcsapi_responses(entries):
            # Process only succeeded ones.
            if not response['api_result']:
                self._logger.warn('KCSAPI request on {} failed.'.format(
                    api_name))
                continue
            for obj in self.dispatch(api_name, request, response):
                yield obj
