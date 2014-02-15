#!/usr/bin/env python
"""JSON serializable object and properties.

This module provides an interface of JSON serializable Python objects,
:class:`JSONSerializableObject`, and concise but powerful ways to define
exportable properties.

A short example illustrating what this module does:

>>> class SomeObject(JSONSerializableObject):
...     foo = JSONProperty('foo', default='FOO')
...     bar = ReadonlyJSONProperty('bar', '_bar')
...
...     @jsonproperty
...     def baz(self):
...         return ':'.join([self.foo, self.bar])
...
>>> s = SomeObject(bar='BAR')
>>> s.foo
'FOO'
>>> s.foo = 'FOOFOO'
>>> s.bar = 'BARBAR'
Traceback (most recent call last):
    ...
AttributeError: Not settable
>>> s.baz
'FOOFOO:BAR'
>>> s.json(sort_keys=True)
'{"bar": "BAR", "baz": "FOOFOO:BAR", "foo": "FOOFOO"}'
"""

import json


class JSONSerializableObject(object):
    """Object serializable to JSON."""

    def __init__(self, **kwargs):
        self_class = self.__class__
        for key, value in kwargs.iteritems():
            if not hasattr(self_class, key):
                raise AttributeError('{}.{} not found'.format(
                    self_class.__name__, key))
            member = getattr(self_class, key)
            member_class = member.__class__
            if not issubclass(member_class, CustomizableJSONProperty):
                raise AttributeError(
                    '{}.{} is {}, not CustomizableJSONProperty'
                    .format(self_class.__name__, key, member_class))
            if issubclass(member_class, ReadonlyJSONProperty):
                setattr(self, member._wrapped_variable, value)
            else:
                setattr(self, key, value)

    def json(self, *args, **kwargs):
        """Serialize this object to JSON."""
        return json.dumps(self, *args, cls=_JSONSerializableObjectEncoder,
                          **kwargs)

    def _serialize_json(self):
        cls = self.__class__
        data = {}
        for attr in cls.__dict__.itervalues():
            if not issubclass(attr.__class__, CustomizableJSONProperty):
                continue
            value = attr.__get__(self)
            if not attr.omittable or value is not None:
                data[attr.name] = value
        return self.json_custom(data)

    def json_custom(self, data):
        """Called when automatic export is done."""
        return data


class _JSONSerializableObjectEncoder(json.JSONEncoder):
    """Encoder which tries to encode :class:`JSONSerializableObject` in
    addition to JSON primitives."""

    def default(self, obj):
        try:
            return obj._serialize_json()
        except:
            super(_JSONSerializableObjectEncoder, self).default(obj)


class CustomizableJSONProperty(object):
    """Property which is exported when the owner object is serialized to JSON.

    :param function fget: getter function
    :param function fset: setter function
    :param function fdel: deleter function
    :param str doc: docstring
    :param str name: name of this property used in JSON
    :param bool omittable: True if this property can be omitted if the value is
                           None

    This is the real property object created when ``@jsonproperty`` decorator
    is used. Using this class directly is discouraged; use :data:`jsonproperty`
    for readability and consistency.

    This class or ``@jsonproperty`` decorator is fully compatible with the
    standard ``@property`` decorator. However, by definition, the property
    should be at least readable (otherwise the object cannot be serialized).
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None, name=None,
                 omittable=True):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc
        self.name = name
        if not name and fget:
            self.name = fget.__name__
        self.omittable = omittable

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
        """Handle ``@jsonproperty.getter`` notation."""
        return self.__class__(fget, self.fset, self.fdel, self.__doc__,
                              self.name, self.omittable)

    def setter(self, fset):
        """Handle ``@jsonproperty.setter`` notation."""
        return self.__class__(self.fget, fset, self.fdel, self.__doc__,
                              self.name, self.omittable)

    def deleter(self, fdel):
        """Handle ``@jsonproperty.deleter`` notation."""
        return self.__class__(self.fget, self.fset, fdel, self.__doc__,
                              self.name, self.omittable)


jsonproperty = CustomizableJSONProperty
"""Alias of :class:`CustomizableJSONProperty`, and intended to be used as a
decorator notation (i.e. ``@jsonproperty``).

Except for the fact that this property will be automatically exported when the
container object's :meth:`JSONSerializableObject.json` is called, you can treat
the property attribute just like one created with the standard ``@property``
decorator.

For example, you can write a JSON serializable object like this:

>>> class SomeObject(JSONSerializableObject):
...
...     def __init__(self):
...         self._b = 'bar'
...
...     # Just like @property, this will create a gettable property named
...     # "a". By default the JSON field name matches the name of property.
...     # Note that you have to return a JSON serializable value from getters;
...     # JSON primitives (e.g. integers, floating-point values, strings, etc.)
...     # or JSONSerializableObject.
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
...     # You can change this behavior by setting omittable=False.
...     # Such a property will be exported with a value of null.
...     @jsonproperty(omittable=False)
...     def d(self):
...         return None

This class would behave like this:

>>> s = SomeObject()
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
``omittable=False``.
"""


class JSONProperty(CustomizableJSONProperty):
    """Property which supports default getter/setter, and is exported when
    the owner object is serialized to JSON.

    This is a simplified version of :class:`CustomizableJSONProperty` for a
    trivial JSON property. This property supports basic getter/setter so that
    a user doesn't need to write all boilerplate accessors. Deletion is not
    supported.

    Example usage of this class:

    >>> class SomeObject(JSONSerializableObject):
    ...     foo = JSONProperty('foo')

    Just this, you're done. You don't need to write a getter or setter.
    Then you can set or read a value just like a usual property.

    >>> s = SomeObject()
    >>> s.foo = 'FOO'
    >>> s.foo
    'FOO'
    >>> del s.foo
    Traceback (most recent call last):
        ...
    AttributeError: Not deletable
    >>> s.json()
    '{"foo": "FOO"}'
    """

    def __init__(self, name, omittable=True, default=None):
        # Note that we can't have a single value in this JSONProperty object.
        # A JSONProperty will be a class variable, and shared among all the
        # instances of that class. They are all owner instances.
        # Possible solution would be to:
        # - Have an owner-to-value map in JSONProperty, or
        # - Store the value to a wrapped variable of each owner
        # Here we choose the latter approach to be consistent with
        # ReadonlyJSONProperty.
        # Of course, there is a chance of conflict if we do the latter, but in
        # reality it almost never happens if we use a namespace like this:
        self._wrapped_variable = ('__kcaa.kcsapi.jsonobject.JSONProperty_{:x}'
            .format(id(self)))
        self._default = default
        super(JSONProperty, self).__init__(fget=self._get, fset=self._set,
                                           name=name, omittable=omittable)

    def _get(self, owner):
        if not hasattr(owner, self._wrapped_variable):
            self._set(owner, self._default)
            return self._default
        else:
            return getattr(owner, self._wrapped_variable)

    def _set(self, owner, value):
        setattr(owner, self._wrapped_variable, value)


class ReadonlyJSONProperty(CustomizableJSONProperty):
    """Property which provides readonly access to a private variable of the
    owner object, and is exported when the owner object is serialized to JSON.

    This is a simplified version of :class:`CustomizableJSONProperty` for a
    trivial and readonly JSON property. This property support a transparent
    getter to a private variable of the owner object, without writing a
    boilerplate getter method.

    Let's see an exmaple:

    >>> class SomeObject(JSONSerializableObject):
    ...     def __init__(self, foo):
    ...         self._foo = foo
    ...
    ...     foo = ReadonlyJSONProperty('foo', '_foo')

    Then, ``foo`` provides a transparent readonly access to a private variable
    ``SomeObject._foo``.

    >>> s = SomeObject('FOO')
    >>> s.foo
    'FOO'
    >>> s.json()
    '{"foo": "FOO"}'
    >>> s.foo ='BAR'
    Traceback (most recent call last):
        ...
    AttributeError: Not settable
    >>> del s.foo
    Traceback (most recent call last):
        ...
    AttributeError: Not deletable
    >>> t = SomeObject('BAR')
    >>> t.foo
    'BAR'
    >>> t.json()
    '{"foo": "BAR"}'
    """

    def __init__(self, name, wrapped_variable=None, omittable=True,
                 default=None):
        if not wrapped_variable:
            wrapped_variable = ('__kcaa.kcsapi.jsonobject.'
                                'ReadonlyJSONProperty_{:x}'.format(id(self)))
        self._wrapped_variable = wrapped_variable
        self._default = default
        super(ReadonlyJSONProperty, self).__init__(fget=self._get, name=name,
                                                   omittable=omittable)

    def _get(self, owner):
        if not hasattr(owner, self._wrapped_variable):
            setattr(owner, self._wrapped_variable, self._default)
            return self._default
        else:
            return getattr(owner, self._wrapped_variable)


if __name__ == '__main__':
    import jsonobject_test
    jsonobject_test.main()
