#!/usr/bin/env python
"""JSON serializable object and properties.

This module contains some basic model of all KCAA objects, which are handled in
the controller, or transmitted to the client.

An example usage of :class:`JsonSerializableObject` would be:

>>> class SampleObject(JsonSerializableObject):
...     @jsonproperty
...     def foo(self):
...         return 'FOO'
>>> s = SampleObject()
>>> s.json()
'{"foo": "FOO"}'
"""

import json


class JsonSerializableObject(object):
    """Object serializable to JSON."""

    def json(self, *args, **kwargs):
        """Serialize this object to JSON."""
        return json.dumps(self, *args, cls=_JsonSerializableObjectEncoder,
                          **kwargs)

    def _serialize_json(self):
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


class _JsonSerializableObjectEncoder(json.JSONEncoder):

    def default(self, obj):
        try:
            return obj._serialize_json()
        except:
            super(_JsonSerializableObjectEncoder, self).default(obj)


class JsonCustomizableProperty(object):
    """Property which is serialized when the object is converted to JSON.

    :param function fget: getter function
    :param function fset: setter function
    :param function fdel: deleter function
    :param str doc: docstring
    :param str name: name of this property used in JSON
    :param bool store_if_null: True if this property will be stored in JSON
                               even if None

    This is the real property object created when ``@jsonproperty`` decorator
    is used. Using this class directly is discouraged; use :data:`jsonproperty`
    for readability and consistency.

    This class or ``@jsonproperty`` decorator is fully compatible with the
    standard ``@property`` decorator. However, by definition, the property
    should be at least readable (otherwise the object cannot be serialized).
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None, name=None,
                 store_if_null=False):
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
...         self._b = 'bar'
...
...     # Just like @property, this will create a gettable property named
...     # "a". Nore that you have to return a JSON primitives, or
...     # JsonSerializableObject, as a value of this property.
...     @jsonproperty
...     def a(self):
...         return 'foo'
...
...     # You can change the name of an exported JSON field. This property will
...     # be accessible via "beta" field in JSON.
...     @jsonproperty(name='beta')
...     def b(self):
...         return self._b
...
...     # You can define a setter and deleter too, if you'd like to.
...     @b.setter
...     def b(self, value):
...         self._b = value
...
...     # By default, a property will be omitted in JSON if the value is None.
...     @jsonproperty
...     def c(self):
...         return None
...
...     # You can change this behavior by setting store_if_null=True.
...     # Such a property will be exported with a value of null.
...     @jsonproperty(store_if_null=True)
...     def d(self):
...         return None

This class would behave like this:

>>> s = SampleObject()
>>> s.a
'foo'
>>> s.b
'bar'
>>> s.b = 'BAR'
>>> s.b
'BAR'
>>> s.c
>>> s.d
>>> s.json(sort_keys=True)
'{"a": "foo", "beta": "BAR", "d": null}'

Note that ``b`` is exported as ``beta`` due to ``name='beta'``. Also note that
``c`` is not exported because it returns None. ``d`` is still exported due to
``store_if_null=True``.
"""


class JsonProperty(JsonCustomizableProperty):
    """Property which supports default fetch/store actions, and is serialized
    when the object is converted to JSON.

    This is a simplified version of :class:`JsonCustomizableProperty` for a
    trivial JSON property. This property supports basic fetch/store actions so
    that a user doesn't need to write all boilerplate getter/setter pairs.

    Example usage of this class:

    >>> class SomeObject(JsonSerializableObject):
    ...     foo = JsonProperty('foo')

    Just this, you're done. You don't need to write a getter, setter or
    deleter. Then you can set or read a value just like a usual property.

    >>> s = SomeObject()
    >>> s.foo = 'FOO'
    >>> s.foo
    'FOO'
    >>> s.json()
    '{"foo": "FOO"}'
    """

    def __init__(self, name, store_if_null=False, default=None):
        self._value = default
        super(JsonProperty, self).__init__(fget=self._get, fset=self._set,
                                           fdel=self._delete, name=name,
                                           store_if_null=store_if_null)

    def _get(self, owner):
        return self._value

    def _set(self, owner, value):
        self._value = value

    def _delete(self, owner):
        del self._value


class ReadonlyJsonProperty(JsonCustomizableProperty):
    """Property which provides readonly access to a private variable of the
    owner object, and is serialized when the object is converted to JSON.

    This is a simplified version of :class:`JsonCustomizableProperty` for a
    trivial and readonly JSON property. This property support a transparent
    fetch action to a private instance variable of the owner object, without
    writing a boilerplate getter method.

    Let's see an exmaple:

    >>> class SomeObject(JsonSerializableObject):
    ...     def __init__(self, foo):
    ...         self._foo = foo
    ...
    ...     foo = ReadonlyJsonProperty('foo', '_foo')

    Then, ``foo`` provides a transparent readonly access to a private instance
    variable ``SomeObject._foo``.

    >>> s = SomeObject('FOO')
    >>> s.foo
    'FOO'
    >>> s.json()
    '{"foo": "FOO"}'
    >>> t = SomeObject('BAR')
    >>> t.foo
    'BAR'
    >>> t.json()
    '{"foo": "BAR"}'
    """

    def __init__(self, name, wrapped_variable, store_if_null=False):
        self._wrapped_variable = wrapped_variable
        super(ReadonlyJsonProperty, self).__init__(fget=self._get, name=name,
                                                   store_if_null=store_if_null)

    def _get(self, owner):
        return getattr(owner, self._wrapped_variable)


if __name__ == '__main__':
    import jsonobject_test
    jsonobject_test.main()
