#!/usr/bin/env python
"""JSON serializable object and properties.

This module contains some basic model of all KCAA objects, which are handled in
the controller, or transmitted to the client.

An example usage of :class:`JsonSerializableObject` would be:

>>> class SampleObject(JsonSerializableObject):
...     @jsonproperty
...     def field_foo(self):
...         return 'foo'
>>> s = SampleObject()
>>> s.json()
'{"field_foo": "foo"}'
"""

import json


class JsonSerializableObject(object):
    """Object serializable to JSON."""

    def json(self, *args, **kwargs):
        """Serialize this object to JSON."""
        return json.dumps(self, *args, cls=JsonSerializableObjectEncoder,
                          **kwargs)

    def _serialize_json(self):
        """Automatically find properties to export."""
        cls = self.__class__
        data = {}
        for attr in cls.__dict__.itervalues():
            if not isinstance(attr, JsonCustomizableProperty):
                continue
            if attr.store_if_null:
                data[attr.name] = attr.__get__(self)
            value = attr.__get__(self)
            if value:
                data[attr.name] = value
        return self.format_custom(data)

    def format_custom(self, data):
        """Called when automatic export is done."""
        return data


class JsonSerializableObjectEncoder(json.JSONEncoder):

    def default(self, obj):
        try:
            return obj._serialize_json()
        except:
            super(JsonSerializableObjectEncoder, self).default(obj)


class JsonCustomizableProperty(object):
    """Property which is serialized when the object is converted to JSON.

    This is the real property object created when ``@jsonproperty`` decorator
    is used. See :data:`jsonproperty` for usage.

    This class or ``@jsonproperty`` decorator is compatible with the standard
    ``@property`` decorator. However, by definition, the property should be at
    least readable.
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None, name=None,
                 store_if_null=True):
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
            raise AttributeError('Not gettable')
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


jsonproperty = JsonCustomizableProperty
"""This is an alias of :class:`JsonCustomizableProperty`, and intended to be
used as a decorator notation (i.e. ``@jsonproperty``).

Except for the fact that this property will be automatically exported when the
container object's :meth:`JsonSerializableObject.json` is called, you can treat
the property attribute just like one created with the standard ``@property``
decorator.

For example, you can write a JSON serializable object like this:

>>> class SampleObject(JsonSerializableObject):
...
...     def __init__(self):
...         self._bar = 'bar'
...
...     # Just like @property, this will create a gettable property named
...     # "field_foo".
...     @jsonproperty
...     def field_foo(self):
...         return 'foo'
...
...     # You can change the name of field when exported to JSON.
...     # Of course, from Python code, this is accessible as "field_bar".
...     @jsonproperty(name='debug_bar')
...     def field_bar(self):
...         return self._bar
...
...     # You can define a setter and deleter too, if you'd like to.
...     @field_bar.setter
...     def field_bar(self, value):
...         self._bar = value
...
...     # You can omit some field if the value is None (null in JSON) by
...     # setting store_if_null=False.
...     # By default, all ``@jsonproperty`` objects are always exported.
...     @jsonproperty(store_if_null=False)
...     def field_baz(self):
...         return None

This class would behave like this:

>>> s = SampleObject()
>>> s.field_foo
'foo'
>>> s.field_bar
'bar'
>>> s.field_bar = 'BAR'
>>> s.field_bar
'BAR'
>>> s.field_baz
>>> s.json(sort_keys=True)
'{"debug_bar": "BAR", "field_foo": "foo"}'

Note that ``field_bar`` is exported as ``debug_bar`` due to
``@jsonproperty(name='debug_bar')``, and ``field_baz`` is *not* exported
because it's annotated as ``@jsonproperty(store_if_null=False)`` and returns
None.
"""
