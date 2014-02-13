#!/usr/bin/env python

import json


class KcaaObject(object):

    def __init__(self, api_name, response, debug):
        self.api_names = set()
        self.debug = debug
        self.update(api_name, response)

    @property
    def object_type(self):
        return self.__class__.__name__

    def update(self, api_name, response):
        self.api_names.add(api_name)
        if self.debug:
            self.response = response

    def format_data(self, data):
        data['_api_names'] = sorted(list(self.api_names))
        if self.debug:
            data['_raw_response'] = self.response
        return json.dumps(data, encoding='utf8')
