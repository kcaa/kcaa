#!/usr/bin/env python

import json


class KcaaObject(object):

    def __init__(self, api_name, response, debug):
        self.api_names = set((api_name))
        self.debug = debug
        if debug:
            self.response = response

    @property
    def object_type(self):
        return self.__class__.__name__

    def update(self, api_name, result):
        self.api_names.add(api_name)
        if self.debug:
            self.response = result.response

    def format_data(self, data):
        data['_api_names'] = sorted(list(self.api_names))
        if self.debug:
            data['_raw_response'] = self.response
        return json.dumps(data, encoding='utf8')
