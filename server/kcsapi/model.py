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


class JsonSerializableObject(object):

    def json(self, *args, **kwargs):
        return json.dumps(self, *args, cls=JsonSerializableObjectEncoder,
                          **kwargs)

    def _serialize_json(self):
        cls = self.__class__
        data = {}
        for attr in cls.__dict__.itervalues():
            if not isinstance(attr, JsonSerializedProperty):
                continue
            if attr._store_if_null:
                data[attr._name] = attr.__get__(self)
            value = attr.__get__(self)
            if value:
                data[attr._name] = value
        return self._serialize_json_custom(data)

    def _serialize_json_custom(self, data):
        return data


class JsonSerializableObjectEncoder(json.JSONEncoder):

    def default(self, obj):
        try:
            return obj._serialize_json()
        except:
            raise
            super(JsonSerializableObjectEncoder, self).default(obj)


class JsonSerializedProperty(object):

    def __init__(self, func=None, name=None, store_if_null=None):
        """Create JSON serialized property.

        The first positional parameter will be used when decorated without
        arguments.
        """
        self._func = func
        self._name = name
        if not name and func:
            self._name = func.__name__
        self._store_if_null = store_if_null

    def __call__(self, func):
        """Handle parameterized JSON serialized property."""
        self._func = func
        if not self._name:
            self._name = func.__name__
        return self

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return self._func(obj)


# Provide lower-cased version that looks more natural.
json_serialized_property = JsonSerializedProperty


if __name__ == '__main__':
    import model_test
    model_test.main()
