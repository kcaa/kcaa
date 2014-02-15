#!/usr/bin/env python

import pytest

import jsonobject
from jsonobject import jsonproperty


class TestJSONSerializableObject(object):

    def test_default_getter(self):

        class SomeObject(jsonobject.JSONSerializableObject):
            # @jsonproperty creates a property which is exported to a
            # serialized JSON of SomeObject.
            # It can decorate without any arguments.
            @jsonproperty
            def foo(self):
                return 'FOO'

        s = SomeObject()
        # "foo" can be used as a normal getter.
        assert s.foo == 'FOO'
        # And is automatically exported.
        assert s.json() == '{"foo": "FOO"}'

    def test_named_getter(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            # This field is exported as "field_foo".
            # Note that in @jsonproperty specs, parameters should be named; you
            # can't do this way:
            # @jsonproperty('field_foo')
            @jsonproperty(name='field_foo')
            def foo(self):
                return 'FOO'

        s = SomeObject()
        assert s.foo == 'FOO'
        assert s.json() == '{"field_foo": "FOO"}'

    def test_not_exported_if_null(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            def __init__(self, value):
                self.value = value

            # If store_if_null is False, the property will not exported.
            # This is the default behavior if omitted.
            @jsonproperty(store_if_null=False)
            def foo(self):
                return self.value

        assert SomeObject('FOO').json() == '{"foo": "FOO"}'
        assert SomeObject('').json() == '{"foo": ""}'
        assert SomeObject(0).json() == '{"foo": 0}'
        assert SomeObject(None).json() == '{}'

    def test_exported_if_null(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            def __init__(self, value):
                self.value = value

            # If store_if_null is True, the property will always be exported.
            @jsonproperty(store_if_null=True)
            def foo(self):
                return self.value

        assert SomeObject('FOO').json() == '{"foo": "FOO"}'
        assert SomeObject('').json() == '{"foo": ""}'
        assert SomeObject(0).json() == '{"foo": 0}'
        assert SomeObject(None).json() == '{"foo": null}'

    def test_non_primitive_value(self):
        class NonPrimitiveObject(object):
            pass

        class SomeObject(jsonobject.JSONSerializableObject):
            # The getter cannot return a non JSON primitive value.
            @jsonproperty
            def foo(self):
                return NonPrimitiveObject()

        with pytest.raises(TypeError):
            SomeObject().json()

    def test_non_primitive_serializable_value_getter(self):
        class NonPrimitiveSerializableObject(
                jsonobject.JSONSerializableObject):
            @jsonproperty
            def child_foo(self):
                return 'CHILD_FOO'

        class SomeObject(jsonobject.JSONSerializableObject):
            # OK if the non primitive value is JSON serializable.
            @jsonproperty
            def foo(self):
                return NonPrimitiveSerializableObject()

        assert SomeObject().json() == '{"foo": {"child_foo": "CHILD_FOO"}}'

    def test_setter_and_deleter(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            def __init__(self, foo):
                self._foo = foo

            @jsonproperty
            def foo(self):
                return self._foo

            # Setter can be used just like the standard property.
            @foo.setter
            def foo(self, foo):
                self._foo = foo

            # The same for deleter. You should reset the value before caalling
            # json(), though.
            @foo.deleter
            def foo(self):
                del self._foo

        s = SomeObject('FOO')
        assert s.foo == 'FOO'
        assert s.json() == '{"foo": "FOO"}'
        s.foo = 'BAR'
        assert s.foo == 'BAR'
        assert s.json() == '{"foo": "BAR"}'
        del s.foo
        # Accessing a deleted property will raise AttributeError.
        with pytest.raises(AttributeError):
            s.foo
        # And trying to convert the container object to JSON will raise
        # TypeError.
        with pytest.raises(TypeError):
            s.json()
        # Resetting the property will make the conversion possible again.
        s.foo = "BAZ"
        assert s.json() == '{"foo": "BAZ"}'

    def test_json_property(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            # This does the same thing as @jsonproperty getter, setter and
            # deleter.
            # Note that the JSON name is mandatory. It can be a positional
            # argument.
            foo = jsonobject.JSONProperty('foo')

        s = SomeObject()
        # The property defaults to None.
        assert s.foo is None
        s.foo = 'FOO'
        assert s.foo == 'FOO'
        assert s.json() == '{"foo": "FOO"}'
        del s.foo
        with pytest.raises(AttributeError):
            s.foo

    def test_json_property_default(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            # default speficies the default value of the property.
            foo = jsonobject.JSONProperty('foo', default='FOO')

        s = SomeObject()
        assert s.foo == 'FOO'
        s.foo = 'BAR'
        assert s.foo == 'BAR'

    def test_json_property_init(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            foo = jsonobject.JSONProperty('foo')
            bar = object()

        # JSONSerializableObject constructor accepts key-value specifications
        # for JSONProperty.
        s = SomeObject(foo='FOO')
        assert s.foo == 'FOO'
        # It doesn't accept setting a value to non-JSONProperty objects.
        with pytest.raises(AttributeError):
            s = SomeObject(bar='BAR')
        # It also rejects creating a new member.
        with pytest.raises(AttributeError):
            s = SomeObject(baz='BAZ')

    def test_json_readonly_property(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            def __init__(self, foo):
                self._foo = foo

            # This property exports SomeObject._foo in a readonly manner.
            foo = jsonobject.ReadonlyJSONProperty('foo', '_foo')

        s = SomeObject('FOO')
        assert s.foo == 'FOO'
        # Client code cannot assign a value to s.foo.
        with pytest.raises(AttributeError):
            s.foo = 'BAR'
        assert s.json('{"foo": "FOO"}')

    def test_readonly_json_property_init(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            # If wrapped_variable is omitted, the property tries to wrap one
            # with the name prepended by '_': foo wraps '_foo', and bar wraps
            # '_bar'.
            foo = jsonobject.ReadonlyJSONProperty('foo')
            bar = jsonobject.ReadonlyJSONProperty('bar')
            # This class member's name conflicts with the name of the wrapped
            # variable of bar, which is '_bar'.
            _bar = 'CLASS_BAR'
            # bar wraps '_baz_unique'.
            # Use this explicit declaration if you really want. However, you
            # may want to avoid prepending an underscore (_) to class members.
            baz = jsonobject.ReadonlyJSONProperty('baz', '_baz_unique')
            # Anyways, this should not conflict.
            _baz = 'CLASS_BAZ'

        # JSONSerializableObject constructor accepts key-value specifications
        # for ReadonlyJSONProperty too. It creates a private variable with the
        # name of wrapped_varaible.
        s = SomeObject(foo='FOO')
        assert s.foo == 'FOO'
        assert s._foo == 'FOO'
        # bar uses _bar as a wrapped variable, and the name conflicts with an
        # existing class variable.
        # Key-value specs in the constructor never overwrite class variables.
        # It is tricky, however, so you might want to avoid this kind of
        # conflicts.
        s = SomeObject(bar='BAR')
        assert s.bar == 'BAR'
        assert s._bar == 'BAR'
        assert SomeObject._bar == 'CLASS_BAR'
        # baz doesn't conflict; though there is _baz in SomeObject, baz
        # property wraps _baz_unique.
        s = SomeObject(baz='BAZ')
        assert s.baz == 'BAZ'
        assert s._baz_unique == 'BAZ'
        assert s._baz == 'CLASS_BAZ'
        assert SomeObject._baz == 'CLASS_BAZ'

    def test_readonly_json_property_default(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            foo = jsonobject.ReadonlyJSONProperty('foo', default='FOO')

        assert SomeObject().foo == 'FOO'
        assert SomeObject(foo='BAR').foo == 'BAR'


def main():
    import doctest
    doctest.testmod(jsonobject)
    pytest.main(args=[__file__.replace('.pyc', '.py')])


if __name__ == '__main__':
    main()