#!/usr/bin/env python

import base64
import json
import logging
import re
import urlparse

import kcsapi


KCSAPI_PATH_REGEX = re.compile(r'/kcsapi(?P<api_name>/.*)')
KCSAPI_PREFIX = 'svdata='

KCSAPI_HANDLERS = {
    '/api_get_member/questlist': [kcsapi.QuestList],
}


class KcsapiHandler(object):

    def __init__(self, har_manager):
        self._logger = logging.getLogger('kcaa.kcsapi_util')
        self.har_manager = har_manager
        self.debug = True
        self.objects = {}

    def get_kcsapi_responses(self, har):
        for entry in har['log']['entries']:
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
            self._logger.debug('Accessed KCSAPI: {}'.format(api_name))
            for handler in KCSAPI_HANDLERS[api_name]:
                object_type = handler.__name__
                old_obj = self.objects.get(object_type)
                if not old_obj:
                    obj = handler(api_name, response, self.debug)
                    self.objects[object_type] = obj
                else:
                    old_obj.update(api_name, response)
                    obj = old_obj
                yield obj
        except KeyError:
            self._logger.debug('Unknown KCSAPI: {}'.format(api_name))

    def get_updated_objects(self):
        har = self.har_manager.get_next_page()
        if not har:
            return
        for api_name, response in self.get_kcsapi_responses(har):
            for obj in self.dispatch(api_name, response):
                yield obj
