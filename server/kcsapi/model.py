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
        if self.debug:
            data['_api_names'] = sorted(list(self.api_names))
            data['_raw_response'] = self.response
        return json.dumps(data, encoding='utf8')

    @property
    def data(self):
        return self.format_data({})


class DefaultObject(KcaaObject):

    def update(self, api_name, response):
        super(DefaultObject, self).update(api_name, response)
        assert len(self.api_names) == 1

    @property
    def object_type(self):
        return list(self.api_names)[0]


class DefaultHandler(object):

    def __init__(self, api_name):
        self.api_name = api_name

    @property
    def __name__(self):
        return self.api_name

    def __call__(self, *args, **kwargs):
        return DefaultObject(*args, **kwargs)
