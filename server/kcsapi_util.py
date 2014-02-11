#!/usr/bin/env python

import re
import urlparse


KCSAPI_PATH_REGEX = re.compile(r'/kcsapi(?P<api_name>/.*)')


def get_kcsapi_entries(har):
    for entry in har['log']['entries']:
        o = urlparse.urlparse(entry['request']['url'])
        match = KCSAPI_PATH_REGEX.match(o.path)
        if match:
            yield match.group('api_name'), entry


def dispatch(api_name, entry):
    pass
