#!/usr/bin/env python

import json


class KcaaObject(object):

    def __init__(self, response, debug):
        self.debug = debug
        if debug:
            self.response = response

    @property
    def object_type(self):
        return self.__class__.__name__

    def update(self, result):
        if self.debug:
            self.response = result.response

    def format_data(self, data):
        if self.debug:
            data['debugInfo'] = self.response
        return json.dumps(data, encoding='utf8')
