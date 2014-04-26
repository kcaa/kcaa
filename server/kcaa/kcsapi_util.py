#!/usr/bin/env python

import base64
import logging
import re
import urlparse

import kcsapi


def reload_modules():
    reload(kcsapi)
    kcsapi.reload_modules()


KCSAPI_PATH_REGEX = re.compile(r'/kcsapi(?P<api_name>/.*)')
KCSAPI_PREFIX = 'svdata='

# UTF-8 Byte Order Mark.
BOM = '\xEF\xBB\xBF'


class KCSAPIHandler(object):

    def __init__(self, har_manager, debug):
        self._logger = logging.getLogger('kcaa.kcsapi_util')
        self.har_manager = har_manager
        self.debug = debug
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
            # /api_start2 now delivers most (all?) master information;
            # invariant data required for modelling, rendering and everything.
            '/api_auth_member/logincheck': [kcsapi.model.NullHandler()],
            '/api_req_member/get_incentive': [kcsapi.model.NullHandler()],
            '/api_start2': [kcsapi.mission.MissionList,
                            kcsapi.ship.ShipDefinitionList],
            # Encyclopedia
            '/api_get_member/book2': [kcsapi.model.NullHandler()],
            # Ships
            '/api_get_member/ship': [kcsapi.ship.ShipList],
            '/api_get_member/ship2': [kcsapi.ship.ShipList],
            '/api_get_member/ship3': [kcsapi.ship.ShipList],
            '/api_req_hensei/lock': [kcsapi.ship.ShipList],
            '/api_req_hokyu/charge': [kcsapi.ship.ShipList],
            '/api_req_kaisou/remodeling': [kcsapi.ship.ShipList],
            '/api_req_kousyou/getship': [kcsapi.ship.ShipList],
            # Port.
            # Like /api_start2, /api_port/port delivers most (all?) member
            # information; variant data for the player, ships, fleets, repair
            # or building docks.
            # TODO: Support all /api_port/port handlers.
            '/api_port/port': [kcsapi.fleet.FleetList,
                               kcsapi.mission.MissionList,
                               kcsapi.ship.ShipList],
            # Fleets (deck).
            '/api_get_member/deck': [kcsapi.fleet.FleetList,
                                     kcsapi.mission.MissionList],
            '/api_req_hensei/change': [kcsapi.model.NullHandler()],
            # Repair docks
            '/api_get_member/ndock': [kcsapi.repair.RepairDock],
            # Quests
            '/api_get_member/questlist': [kcsapi.quest.QuestList],
            '/api_req_quest/start': [kcsapi.model.NullHandler()],
            '/api_req_quest/stop': [kcsapi.model.NullHandler()],
            # Missions
            '/api_get_member/mission': [kcsapi.mission.MissionList],
            '/api_req_mission/start': [kcsapi.model.NullHandler()],
            '/api_req_mission/result': [kcsapi.model.NullHandler()],
            # Items
            #'/api_get_member/useitem': [],
            # Furnitures
            # Not interested in furniture configuration.
            '/api_get_member/furniture': [kcsapi.model.NullHandler()],
        }
        # Eager handlers accept all KCSAPI responses regardless of API URL.
        self.kcsapi_eager_handlers = [
            kcsapi.client.Screen,
        ]

    def serialize_objects(self):
        """Serialize objects so that the client can deserialize and restore the
        state."""
        return {key: [value.__class__.__module__, value.__class__.__name__,
                      value.json()]
                for key, value in self.objects.iteritems()}

    def deserialize_objects(self, serialized_objects):
        """Deserialize objects to restore the previous state.

        *IMPORTANT NOTE: this method uses :meth:`eval` to find the module (the
        first value in the list). Do not call this method with a data from an
        untrusted source.*
        """
        namespace = __name__.rpartition('.')[0]
        namespace = namespace + '.' if namespace else ''
        for key, value in serialized_objects.iteritems():
            module_name, class_name, text = value
            if module_name.startswith(namespace):
                module_name = module_name[len(namespace):]
            module = eval(module_name)
            cls = getattr(module, class_name)
            self.objects[key] = cls.parse_text(text)

    def get_kcsapi_responses(self, entries):
        for entry in entries:
            o = urlparse.urlparse(entry['request']['url'])
            match = KCSAPI_PATH_REGEX.match(o.path)
            if match:
                api_name = match.group('api_name')
                request = kcsapi.jsonobject.parse(
                    {param['name']: param['value'] for param in
                     entry['request']['postData']['params']},
                    readonly=True)
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
                response = kcsapi.jsonobject.parse_text(text, readonly=True,
                                                        encoding='utf8')
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
                obj = handler()
                # Handler may return None in case there is no need to handle
                # the KCSAPI response.
                if obj:
                    obj.update(api_name, request, response, self.objects,
                               self.debug)
                    self.objects[object_type] = obj
                    yield obj
            else:
                old_obj.update(api_name, request, response, self.objects,
                               self.debug)
                yield old_obj

    def get_updated_objects(self):
        entries = self.har_manager.get_updated_entries()
        if not entries:
            return
        for api_name, request, response in self.get_kcsapi_responses(entries):
            # Process only succeeded ones.
            if not response.api_result:
                self._logger.warn('KCSAPI request on {} failed.'.format(
                    api_name))
                continue
            for obj in self.dispatch(api_name, request, response):
                yield obj
