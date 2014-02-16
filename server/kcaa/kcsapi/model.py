#!/usr/bin/env python
"""JSON serializable object and properties.

This module contains some basic model of all KCAA objects, which are handled in
the controller, or transmitted to the client.
"""

import jsonobject
from jsonobject import jsonproperty


class KcaaObject(jsonobject.JSONSerializableObject):

    def __init__(self, api_name, response, debug, **kwargs):
        super(KcaaObject, self).__init__(**kwargs)
        self.api_names = set()
        self.debug = debug
        self.update(api_name, response)

    @jsonproperty
    def object_type(self):
        return self.__class__.__name__

    @jsonproperty(name='_api_names')
    def debug_api_names(self):
        if self.debug:
            return sorted(list(self.api_names))

    @jsonproperty(name='_raw_response')
    def debug_raw_response(self):
        if self.debug:
            return self.response

    def update(self, api_name, response):
        self.api_names.add(api_name)
        if self.debug:
            self.response = response


class DefaultObject(KcaaObject):

    @jsonproperty
    def object_type(self):
        return list(self.api_names)[0]

    def update(self, api_name, response):
        super(DefaultObject, self).update(api_name, response)
        assert len(self.api_names) == 1


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
