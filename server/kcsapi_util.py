#!/usr/bin/env python

import re
import urlparse


KCSAPI_PATH_REGEX = re.compile(r'/kcsapi(/.*)')


def get_kcsapi_entries(har):
    for entry in har['log']['entries']:
        o = urlparse.urlparse(entry['request']['url'])
        if KCSAPI_PATH_REGEX.match(o.path):
            yield entry
