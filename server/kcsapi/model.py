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
        """Automatically find properties to export."""
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
        """Called when automatic export is done."""
        return data


class JsonSerializableObjectEncoder(json.JSONEncoder):

    def default(self, obj):
        try:
            return obj._serialize_json()
        except:
            super(JsonSerializableObjectEncoder, self).default(obj)


class JsonSerializedProperty(object):

    def __init__(self, fget=None, fset=None, fdel=None, doc=None, name=None,
                 store_if_null=True):
        """Create JSON serialized property.

        This class or @jsonproperty decorator is compatible with the standard
        @property decorator. However, by definition, the property should be at
        least readable.
        """
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc
        self.name = name
        if not name and fget:
            self.name = fget.__name__
        self.store_if_null = store_if_null

    def __call__(self, fget):
        """Handle parameterized JSON serialized property declaration."""
        self.fget = fget
        if self.__doc__ is None:
            self.__doc__ = fget.__doc__
        if not self.name:
            self.name = fget.__name__
        return self

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError('Not readable')
        return self.fget(obj)

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError('Not settable')
        self.fset(obj, value)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError('Not deletable')
        self.fdel(obj)

    def getter(self, fget):
        return self.__class__(fget, self.fset, self.fdel, self.__doc__,
                              self.name, self.store_if_null)

    def setter(self, fset):
        return self.__class__(self.fget, fset, self.fdel, self.__doc__,
                              self.name, self.store_if_null)

    def deleter(self, fdel):
        return self.__class__(self.fget, self.fset, fdel, self.__doc__,
                              self.name, self.store_if_null)


# Provide lower-cased version that looks more natural.
jsonproperty = JsonSerializedProperty


if __name__ == '__main__':
    import model_test
    model_test.main()
