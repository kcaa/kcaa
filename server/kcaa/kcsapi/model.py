#!/usr/bin/env python
"""JSON serializable object and properties.

This module contains some basic model of all KCAA objects, which are handled in
the controller, or transmitted to the client.
"""

import jsonobject


class KcaaObject(jsonobject.JsonSerializableObject):

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

    def format_custom(self, data):
        if self.debug:
            data['_api_names'] = sorted(list(self.api_names))
            data['_raw_response'] = self.response
        return data


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


if __name__ == '__main__':
    import model_test
    model_test.main()
