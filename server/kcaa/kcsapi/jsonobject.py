#!/usr/bin/env python
"""JSON serializable object and properties.

This module provides an interface of JSON serializable Python objects,
:class:`JSONSerializableObject`, and concise but powerful ways to define
exportable properties.

A short example illustrating what this module does:

>>> class SomeObject(JSONSerializableObject):
...     foo = JSONProperty('foo', 'FOO_DEFAULT')
...     bar = ReadonlyJSONProperty('bar', 'BAR_DEFAULT')
...
...     @jsonproperty
...     def baz(self):
...         return ':'.join([self.foo, self.bar])
...
>>> s = SomeObject(bar='BAR')
>>> s.foo
'FOO_DEFAULT'
>>> s.foo = 'FOOFOO'
>>> s.bar
'BAR'
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
    """Object serializable to JSON.

    :param bool _initialize: True if initialize. Set False if this object will
                             be initialized later
    :param kwargs: arbitrary key-value mapping to initialize JSON properties

    This class represents an object which is serializable to JSON. Typically
    you subclass this class and define exportable properties using:

    * :class:`JSONProperty`, read/write-able simple data holder
    * :class:`ReadonlyJSONProperty`, readonly version of :class:`JSONProperty`
    * :func:`jsonproperty`, which allows you to customize the property

    See examples in this module for how to use them.
    """

    def __init__(self, _initialize=True, **kwargs):
        if _initialize:
            self._initialize(kwargs, _ignore_unknown=False)
        else:
            self.__overriding_data = kwargs

    def _initialize(self, data, _ignore_unknown=False):
        self_class = self.__class__
        for key, value in data.iteritems():
            if not hasattr(self_class, key):
                if _ignore_unknown:
                    continue
                else:
                    raise AttributeError('{}.{} not found'.format(
                        self_class.__name__, key))
            member = getattr(self_class, key)
            member_class = member.__class__
            if not issubclass(member_class, CustomizableJSONProperty):
                raise AttributeError(
                    '{}.{} is {}, not CustomizableJSONProperty'
                    .format(self_class.__name__, key, member_class))
            if issubclass(member_class, JSONProperty):
                value = JSONSerializableObject._replace_containers(
                    value, member._value_type, member._element_type,
                    _ignore_unknown=_ignore_unknown)
            if issubclass(member_class, ReadonlyJSONProperty):
                member._initialize(self, value)
            else:
                setattr(self, key, value)

    @staticmethod
    def _replace_containers(value, value_type, element_type,
                            _ignore_unknown=False):
        # Try to parse as JSONSerializableObject if the value type is
        # specified and the value is a dict.
        if (isinstance(value, dict) and
                issubclass(value_type, JSONSerializableObject)):
            return value_type.parse(value, _ignore_unknown=_ignore_unknown)
        elif isinstance(value, list) and issubclass(value_type, list):
            # This way we can't define schema that contains a list of list of
            # some type. That should rarely happen, and we don't support such
            # cases. Maybe one can create a special JSONSerializableObject for
            # list.
            return [JSONSerializableObject._replace_containers(
                v, element_type, None, _ignore_unknown=_ignore_unknown) for
                v in value]
        else:
            return value

    def json(self, *args, **kwargs):
        """Serialize this object to JSON.

        :param args: arbitrary positional arguments passed to
                     :func:`json.dumps`
        :param kwargs: arbitrary keyword arguments passed to :func:`json.dumps`
        :returns: JSON representation of this object
        :rtype: string
        :raises TypeError: if this object contains non-serializable object

        Serialize this object to JSON. This is done by creating a map
        constructed by exportable properties. If a property returns a
        non-primitive, such an object will be serialized recursively.
        """
        return json.dumps(self, *args, cls=_JSONSerializableObjectEncoder,
                          **kwargs)

    def _serialize_json(self):
        data = {}
        for key in dir(self):
            attr = None
            # Tries to find a property from the current instance. This is not
            # for an ordinary property, because they are owned by class
            # objects. Properties created dynamically at the instance creation
            # time without creating a dynamic class would fall into this case,
            # but they should be really rare.
            if key in self.__dict__:
                attr = getattr(self, key)
            else:
                # This path is the normal flow.
                # To get a CustomizableJSONProperty instance itself, not a
                # computed value (the result of
                # CustomizableJSONProperty.__get__()), we need to go through
                # MRO to find the class that defines the property.
                for cls in self.__class__.__mro__:
                    if key in cls.__dict__:
                        attr = getattr(cls, key)
                        break
            if attr is None:
                # Special attributes like __doc__ cannot be found in the above
                # way, but can be ignored.
                continue
            if not issubclass(attr.__class__, CustomizableJSONProperty):
                continue
            value = attr.__get__(self)
            if not attr.omittable or value is not None:
                data[attr.name] = value
        return self.postprocess(data)

    def postprocess(self, data):
        """Postprocess the automatically exported data.

        :param map data: map representing this object

        This is a callback method which will be called at the end of export.
        The parameter ``data`` contains all the exported properties' data.
        Usually you don't have to override this method, but if some properties
        need to interact with each other, you can implement such logic here.
        """
        return data

    # TODO: Write example code.
    @classmethod
    def parse_text(cls, text, _ignore_unknown=False, *args, **kwargs):
        """Parse JSON text and creates a typed :class:`JSONSerializaObject`.

        :param text: text representing JSON object
        :type text: str or unicode
        :param bool ignore_unknown: True if ignoring unknown properties
        :param args: arbitrary positional arguments passed to
                     :func:`json.loads`
        :param kwargs: arbitrary keyword arguments passed to :func:`json.loads`
        :returns: Object parsed from the text
        :rtype: :class:`JSONSerializableObject`
        :raises TypeError: if text doesn't represent a JSON map
        :raises ValueError: if text is ill-formed

        Creates a typed subclass instance of :class:`JSONSerializableObject` by
        parsing the *text* as a JSON. This is a safer option than
        :func:`parse_text` because you can define schema by defining a property
        with value_type expectation.

        The given *text* should be a valid JSON map object representation.
        This is a shorthand for :meth:`parse` and lets you skip calling
        :func:`json.loads`. Note that you can't override values with *kwargs*;
        it's a parameter for :func:`json.loads`.
        """
        return cls.parse(json.loads(text, *args, **kwargs),
                         _ignore_unknown=_ignore_unknown)

    @classmethod
    def parse(cls, obj, _ignore_unknown=False, *args, **kwargs):
        """Creates a typed :class:`JSONSerializableObject` from a Python
        representation of a JSON object.

        :param dict obj: Python representation of a JSON object
        :param bool ignore_unknown: True if ignoring unknown properties
        :param kwargs: arbitrary positional arguments passed to the class'
                       constructor
        :param kwargs: arbitrary keyword arguments passed to the class'
                       constructor
        :returns: Object parsed from the text
        :rtype: :class:`JSONSerializableObject`
        :raises TypeError: if obj is not a dict, or if some type check fails

        If you want your subclass parseable, you shouldn't create a your own
        parameter that needs to be initialized in __init__. Otherwise parsing
        will be failed if that object is being created as a descendant.
        """
        if not isinstance(obj, dict):
            raise TypeError('Given obj is {}, not dict'.format(
                obj.__class__.__name__))
        # At first we don't initialize the object with kwargs. Instead obj is
        # used to initialize, and then kwargs specifications override them.
        parsed_obj = cls(_initialize=False, *args, **kwargs)
        parsed_obj._initialize(obj, _ignore_unknown=_ignore_unknown)
        parsed_obj._initialize(parsed_obj.__overriding_data,
                               _ignore_unknown=False)
        return parsed_obj


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
    is used. It's discouraged to use this class directly. Use
    :func:`jsonproperty` for readability and consistency.
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

:param str name: name of this property used in JSON. Must be a keyword argument
                 if present
:param bool omittable: True if this property can be omitted if the value is
                       None. Must be a keyword argument if present

``@jsonproperty`` decorator creates a customizable JSON property. This behaves
like the standard ``@property`` decorator except for the fact that
``@jsonproperty`` will be taken into account when the owner object is being
serialized; the owner object will call the getter of JSON properties to get a
JSON serializable objects. That means a getter should return JSON primitives
(e.g. string, integer, floating-point value etc.) or any object deriving from
:class:`JSONSerializableObject`.

Remember that ``@jsonproperty`` is fully compatible with the standard
``@property``. You can safely convert an existing property into JSON properties
just by replacing ``@property`` to ``@jsonproperty``. However, if the property
is trivial (i.e. if just encapsulating a private varaible), consider using
:class:`JSONProperty` or :class:`ReadonlyJSONProperty`.

With ``@jsonproperty`` decorators, you can write a JSON serializable object
like this:

>>> class SomeObject(JSONSerializableObject):
...
...     def __init__(self):
...         self._b = 'bar'
...
...     # Just like @property, this will create a gettable property named
...     # "a". By default the property name is used as is when exported to
...     # JSON.
...     # Note that you have to return a JSON serializable value from getters;
...     # either JSON primitives (e.g. string, integer, floating-point value
...     # etc.) or JSONSerializableObject.
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


# TODO: Write example code on value_type
class JSONProperty(CustomizableJSONProperty):
    """Property which supports default getter/setter, and is exported when
    the owner object is serialized to JSON.

    :param str name: name of this property used in JSON
    :param default: default value of the property
    :param type value_type: expected type of the value
    :param type element_type: expected type of the element (if value_type is
                              list)
    :param bool omittable: True if this property can be omitted if the value is
                           None
    :param str wrapped_variable: name of the wrapped variable, or None if using
                                 an automatically chosen one

    This is a read/write-able simple data holder which just behaves like a
    simple variable. This is suitable for a trivial property for which you
    would write boilerplate getter and setter. Deletion is not supported.

    As a JSON property, this will be exported when the owner object is
    serialized to JSON. Common parameters have the same meaning as those of
    :func:`jsonproperty`.

    Example object which has :class:`JSONProperty`:

    >>> class SomeObject(JSONSerializableObject):
    ...     foo = JSONProperty('foo')

    Just this, you're done. Note that the name of the property is mandatory.
    However, you don't need to write a getter or setter.

    Then you can set or get a value just like a usual property.

    >>> s = SomeObject()
    >>> s.foo = 'FOO'
    >>> s.foo
    'FOO'
    >>> s.json()
    '{"foo": "FOO"}'
    >>> del s.foo
    Traceback (most recent call last):
        ...
    AttributeError: Not deletable

    You can set the default value with ``default`` parameter (or the second
    positional parameter). Also you can initialize the object with
    ``name=value`` pairs.

    >>> class AnotherObject(JSONSerializableObject):
    ...     bar = JSONProperty('bar', 'BAR')
    ...
    >>> t = AnotherObject()
    >>> t.bar
    'BAR'
    >>> u = AnotherObject(bar='BARBAR')
    >>> u.bar
    'BARBAR'
    """

    def __init__(self, name, default=None, value_type=None, element_type=None,
                 omittable=True, wrapped_variable=None):
        # Note that we can't have a single value in this JSONProperty object.
        # A JSONProperty will be a class variable, and shared among all the
        # instances of that class. They are all owner instances.
        # Possible solutions include:
        # - Have an owner-to-value map in JSONProperty, or
        # - Store the value to a wrapped variable of each owner
        # Here we choose the latter approach to be consistent with
        # ReadonlyJSONProperty.
        # Of course, there is a chance of conflict if we do the latter, but in
        # reality it almost never happens if we use a namespace like this:
        self._default = default
        self._value_type = value_type
        self._element_type = element_type
        self._check_type(default)
        if not wrapped_variable:
            wrapped_variable = ('__{}_{:x}'.format(self.__class__.__name__,
                                                   id(self)))
        self._wrapped_variable = wrapped_variable
        super(JSONProperty, self).__init__(fget=self._get, fset=self._set,
                                           name=name, omittable=omittable)

    def _get(self, owner):
        if not hasattr(owner, self._wrapped_variable):
            self._set(owner, self._default)
            return self._default
        else:
            return getattr(owner, self._wrapped_variable)

    def _set(self, owner, value):
        self._check_type(value)
        setattr(owner, self._wrapped_variable, value)

    def _check_type(self, value):
        if value is not None and self._value_type is not None:
            if not isinstance(value, self._value_type):
                raise TypeError('Given value {} of type {} is not {}'.format(
                    value, value.__class__.__name__,
                    self._value_type.__name__))
            if (issubclass(self._value_type, list) and
                    self._element_type is not None):
                bad_element = lambda e: not isinstance(e, self._element_type)
                if any(map(bad_element, value)):
                    raise TypeError('Given list {} should contain only '
                                    'elements of type {}'.format(
                                        value, self._element_type.__name__))


class ReadonlyJSONProperty(JSONProperty):
    """Property which provides readonly access to a private variable of the
    owner object, and is exported when the owner object is serialized to JSON.

    :param str name: name of this property used in JSON
    :param default: default value of the property
    :param type value_type: expected type of the value
    :param type element_type: expected type of the element (if value_type is
                              list)
    :param bool omittable: True if this property can be omitted if the value is
                           None
    :param str wrapped_variable: name of the wrapped variable, or None if final

    This is a readonly simple data holder. This is suitable for a trivial
    property for which you would write a boilerplate getter. Setting or
    deletion through this property is not allowed.

    Though the property value cannot be changed by externally, the owner object
    can change the value by making the property *wrap* a private variable of
    it. ``wrapped_variable`` parameter controls this -- see the example below.

    As a JSON property, this will be exported when the owner object is
    serialized to JSON. Common parameters have the same meaning as those of
    :func:`jsonproperty`.

    Example object which has :class:`ReadonlyJSONProperty`:

    >>> class SomeObject(JSONSerializableObject):
    ...     foo = ReadonlyJSONProperty('foo', wrapped_variable='_foo')

    Here ``foo`` wraps a private variable ``SomeObject._foo``. ``foo`` provides
    transparent readonly access to ``_foo`` to client code. The owner object
    should read the value using ``foo``, and set the value using ``_foo``.

    >>> s = SomeObject()
    >>> s._foo = 'FOO'
    >>> s.foo
    'FOO'
    >>> s.json()
    '{"foo": "FOO"}'
    >>> s.foo = 'FOOFOO'
    Traceback (most recent call last):
        ...
    AttributeError: Not settable
    >>> del s.foo
    Traceback (most recent call last):
        ...
    AttributeError: Not deletable

    You can set the default value with ``default`` parameter (or the second
    positional parameter). Also you can initialize the object with
    ``name=value`` pairs.

    >>> class AnotherObject(JSONSerializableObject):
    ...     bar = ReadonlyJSONProperty('bar', 'BAR', wrapped_variable='_bar')
    ...
    >>> t = AnotherObject()
    >>> t.bar
    'BAR'
    >>> u = AnotherObject(bar='BARBAR')
    >>> u.bar
    'BARBAR'

    Also, you can omit ``wrapped_variable`` parameter if you don't need to
    update the value. It's a kind of *final* or really *readonly* variable in
    other languages.

    >>> class YetAnotherObject(JSONSerializableObject):
    ...     qux = ReadonlyJSONProperty('qux')
    ...
    >>> v = YetAnotherObject(qux='QUX')
    >>> v.qux
    'QUX'
    """

    def __init__(self, name, default=None, value_type=None, element_type=None,
                 omittable=True, wrapped_variable=None):
        super(ReadonlyJSONProperty, self).__init__(
            name, default=default, value_type=value_type,
            element_type=element_type, omittable=omittable,
            wrapped_variable=wrapped_variable)

    def _get(self, owner):
        if not hasattr(owner, self._wrapped_variable):
            setattr(owner, self._wrapped_variable, self._default)
            return self._default
        else:
            # Since it requires an extra cost to monitor what value is set to
            # the wrapped variable (it should be possible though), type check
            # is done when a value is being fetched.
            value = getattr(owner, self._wrapped_variable)
            self._check_type(value)
            return value

    # Not settable.
    _set = None

    _initialize = JSONProperty._set


# TODO: Write example code
class DynamicJSONSerializableObject(JSONSerializableObject):
    """Creates a dynamic :class:`JSONSerializableObject` from a Python
    representation of a JSON object.

    :param dict obj: Python representation of a JSON object
    :param bool readonly: True if the resulted object should be readonly
    :param bool omittable: True if a property can be omitted if the value is
                           None
    :param kwargs: arbitrary key-value mapping to override JSON properties
    :raises TypeError: if obj is not a dict
    """

    def __init__(self, obj, readonly=False, omittable=True, **kwargs):
        if not isinstance(obj, dict):
            raise TypeError('Given obj is {}, not dict'.format(
                obj.__class__.__name__))
        # Dynamically create a new type, because properties (to be precise,
        # descriptors) works if and only if owned by a class object.
        cls = type('__{}_{}'.format(self.__class__.__name__, id(self)),
                   (JSONSerializableObject,), dict(self.__class__.__dict__))
        self.__class__ = cls
        if readonly:
            property_type = ReadonlyJSONProperty
        else:
            property_type = JSONProperty
        for key, value in obj.iteritems():
            value = DynamicJSONSerializableObject._replace_containers(
                value, readonly=readonly)
            setattr(cls, key, property_type(key, omittable=omittable,
                                            default=value))
        # Create a property if it's not in the input object.
        for key, value in kwargs.iteritems():
            if not hasattr(cls, key):
                setattr(cls, key, property_type(key, default=value))
        super(cls, self).__init__(**kwargs)

    @staticmethod
    def _replace_containers(value, readonly=False):
        # Recursively create an object if it's a map.
        if isinstance(value, dict):
            return DynamicJSONSerializableObject(value, readonly=readonly)
        elif isinstance(value, list):
            return [DynamicJSONSerializableObject._replace_containers(
                v, readonly=readonly) for v in value]
        else:
            return value


# TODO: Write example code
def parse_text(text, readonly=False, omittable=True, *args, **kwargs):
    """Parse JSON text and creates a dynamic :class:`JSONSerializaObject`.

    :param text: text representing JSON object
    :type text: str or unicode
    :param bool readonly: True if the resulted object should be readonly
    :param bool omittable: True if a property can be omitted if the value is
                           None
    :param args: arbitrary positional arguments passed to :func:`json.loads`
    :param kwargs: arbitrary keyword arguments passed to :func:`json.loads`
    :returns: Object parsed from the text
    :rtype: :class:`JSONSerializableObject`
    :raises TypeError: if text doesn't represent a JSON map
    :raises ValueError: if text is ill-formed

    Creates a :class:`JSONSerializableObject` by parsing the *text* as a JSON.
    It should be a valid JSON map object representation. This is a shorthand
    for :class:`DynamicJSONSerializableObject` and lets you skip calling
    :func:`json.loads`. Note that you can't override values with *kwargs*; it's
    a parameter for :func:`json.loads`.
    """
    return DynamicJSONSerializableObject(json.loads(text, *args, **kwargs),
                                         readonly=readonly,
                                         omittable=omittable)

parse = DynamicJSONSerializableObject
"""Creates a dynamic :class:`JSONSerializableObject` from a Python
representation of a JSON object.

This is an alias of :class:`DynamicJSONSerializableObject` prepared as a
counterpart of :func:`parse_text`. Note that the difference in *args* and
*kwargs*; this function takes *kwargs* for key-value initialization, not for
calling :func:`json.loads`.
"""


if __name__ == '__main__':
    import jsonobject_test
    jsonobject_test.main()
