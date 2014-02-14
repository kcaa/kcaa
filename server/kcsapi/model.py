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
            if attr.store_if_null:
                data[attr.name] = attr.__get__(self)
            value = attr.__get__(self)
            if value:
                data[attr.name] = value
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

    def __init__(self, name, store_if_null, func):
        self.name = name
        self.store_if_null = store_if_null
        self._func = func

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return self._func(obj)


def json_serialized_property(func, name=None, store_if_null=True):
    if not name:
        try:
            name = func.__name__
        except:
            TypeError('Property name cannot be inferred for {}'.format(func))
    return JsonSerializedProperty(name, store_if_null, func)


if __name__ == '__main__':
    import model_test
    model_test.main()
