#!/usr/bin/env python

import base64
import json
import re
import urlparse

import kcsapi


KCSAPI_PATH_REGEX = re.compile(r'/kcsapi(?P<api_name>/.*)')
KCSAPI_PREFIX = 'svdata='

KCSAPI_HANDLERS = {
    '/api_get_member/questlist': [kcsapi.QuestList],
}


def get_kcsapi_responses(har):
    for entry in har['log']['entries']:
        o = urlparse.urlparse(entry['request']['url'])
        match = KCSAPI_PATH_REGEX.match(o.path)
        if match:
            api_name = match.group('api_name')
            content = entry['response']['content']
            text = content['text']
            # Highly likely the KCSAPI response is Base64 encoded, because the
            # API server doesn't attach charset information.
            encoding = content.get('encoding')
            if encoding == 'base64':
                text = base64.b64decode(text)
            # Skip response prefix which makes JSON parsing fail.
            if text.startswith(KCSAPI_PREFIX):
                text = text[len(KCSAPI_PREFIX):]
            else:
                # TODO: Use logger or simply remove this.
                print 'Unexpected KCSAPI response: {}'.format(text)
            # KCSAPI response should be in UTF-8.
            response = json.loads(text, encoding='utf8')
            yield api_name, response


def dispatch(api_name, response, debug):
    try:
        for handler in KCSAPI_HANDLERS[api_name]:
            yield handler(api_name, response, debug)
    except KeyError:
        raise ValueError('Unknown KCSAPI: {}'.format(api_name))
