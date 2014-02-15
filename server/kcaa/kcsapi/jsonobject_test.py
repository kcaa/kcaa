#!/usr/bin/env python

import pytest

import jsonobject
from jsonobject import jsonproperty


class TestJsonSerializableObject(object):

    def test_default_getter(self):

        class SomeObject(jsonobject.JsonSerializableObject):
            # Can decorate without any arguments.
            @jsonproperty
            def foo(self):
                return 'FOO'

        s = SomeObject()
        # "foo" can be used as a normal getter.
        assert s.foo == 'FOO'
        # And is automatically exported.
        assert s.json() == '{"foo": "FOO"}'

    def test_named_getter(self):
        class SomeObject(jsonobject.JsonSerializableObject):
            # This field is exported as "field_foo".
            # Note that parameters should be named; you can't do this way:
            # @jsonproperty('field_foo')
            @jsonproperty(name='field_foo')
            def foo(self):
                return 'FOO'

        s = SomeObject()
        assert s.foo == 'FOO'
        assert s.json() == '{"field_foo": "FOO"}'

    def test_not_exported_if_null(self):
        class SomeObject(jsonobject.JsonSerializableObject):
            def __init__(self, value):
                self.value = value

            # If store_if_null is False, the property will not exported.
            # This is the default behavior if omitted.
            @jsonproperty(store_if_null=False)
            def foo(self):
                return self.value

        assert SomeObject('FOO').json() == '{"foo": "FOO"}'
        assert SomeObject(None).json() == '{}'

    def test_exported_if_null(self):
        class SomeObject(jsonobject.JsonSerializableObject):
            def __init__(self, value):
                self.value = value

            # If store_if_null is True, the property will always be exported.
            @jsonproperty(store_if_null=True)
            def foo(self):
                return self.value

        assert SomeObject('FOO').json() == '{"foo": "FOO"}'
        assert SomeObject(None).json() == '{"foo": null}'

    def test_non_primitive_value(self):
        class NonPrimitiveObject(object):
            pass

        class SomeObject(jsonobject.JsonSerializableObject):
            # The getter cannot return a non JSON primitive value.
            @jsonproperty
            def foo(self):
                return NonPrimitiveObject()

        with pytest.raises(TypeError):
            SomeObject().json()

    def test_non_primitive_serializable_value_getter(self):
        class NonPrimitiveSerializableObject(
                jsonobject.JsonSerializableObject):
            @jsonproperty
            def child_foo(self):
                return 'CHILD_FOO'

        class SomeObject(jsonobject.JsonSerializableObject):
            # OK if the non primitive value is JSON serializable.
            @jsonproperty
            def foo(self):
                return NonPrimitiveSerializableObject()

        assert SomeObject().json() == '{"foo": {"child_foo": "CHILD_FOO"}}'

    def test_setter_and_deleter(self):
        class SomeObject(jsonobject.JsonSerializableObject):
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
        class SomeObject(jsonobject.JsonSerializableObject):
            # This does the same thing as @jsonproperty getter, setter and
            # deleter.
            # Note that the JSON name is mandatory. It can be a positional
            # argument.
            foo = jsonobject.JsonProperty('foo')

        s = SomeObject()
        # The property defaults to None.
        assert s.foo is None
        s.foo = 'FOO'
        assert s.foo == 'FOO'
        assert s.json() == '{"foo": "FOO"}'
        del s.foo
        with pytest.raises(AttributeError):
            s.foo

    def test_json_readonly_property(self):
        class SomeObject(jsonobject.JsonSerializableObject):
            def __init__(self, foo):
                self._foo = foo

            # This property exports SomeObject._foo in a readonly manner.
            foo = jsonobject.ReadonlyJsonProperty('foo', '_foo')

        s = SomeObject('FOO')
        assert s.foo == 'FOO'
        # Client code cannot assign a value to s.foo.
        with pytest.raises(AttributeError):
            s.foo = 'BAR'
        assert s.json('{"foo": "FOO"}')


def main():
    import doctest
    doctest.testmod(jsonobject)
    pytest.main(args=[__file__.replace('.pyc', '.py')])


if __name__ == '__main__':
    main()
