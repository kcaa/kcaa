#!/usr/bin/env python

import pytest

import jsonobject


class TestJsonSerializableObject(object):

    def test_default_getter(self):

        class DefaultGetter(jsonobject.JsonSerializableObject):
            # Can decorate without any arguments.
            @jsonobject.jsonproperty
            def field_foo(self):
                return 'foo'

        g = DefaultGetter()
        # field_foo can be used as a normal getter.
        assert g.field_foo == 'foo'
        # And is automatically exported.
        assert g.json() == '{"field_foo": "foo"}'

    def test_named_getter(self):
        class NamedGetter(jsonobject.JsonSerializableObject):
            # This field is exported as "FOO".
            # Note that parameters should be named; you can't do this way:
            # @jsonobject.jsonproperty('FOO')
            @jsonobject.jsonproperty(name='FOO')
            def field_foo(self):
                return 'foo'

        g = NamedGetter()
        assert g.field_foo == 'foo'
        assert g.json() == '{"FOO": "foo"}'

    def test_not_exported_if_null(self):
        class SomeObject(jsonobject.JsonSerializableObject):
            def __init__(self, value):
                self.value = value

            # If store_if_null is False, the property will not exported.
            # This is the default behavior.
            @jsonobject.jsonproperty(store_if_null=False)
            def field_foo(self):
                return self.value

        assert SomeObject('foo').json() == '{"field_foo": "foo"}'
        assert SomeObject(None).json() == '{}'

    def test_exported_if_null(self):
        class SomeObject(jsonobject.JsonSerializableObject):
            def __init__(self, value):
                self.value = value

            # If store_if_null is True, the property will always be exported.
            @jsonobject.jsonproperty(store_if_null=True)
            def field_foo(self):
                return self.value

        assert SomeObject('foo').json() == '{"field_foo": "foo"}'
        assert SomeObject(None).json() == '{"field_foo": null}'

    def test_non_primitive_value_getter(self):
        class NonPrimitiveObject(object):
            pass

        class NonPrimitiveValueGetter(jsonobject.JsonSerializableObject):
            # The getter cannot return a non primitive value.
            @jsonobject.jsonproperty
            def field_foo(self):
                return NonPrimitiveObject()

        with pytest.raises(TypeError):
            NonPrimitiveValueGetter().json()

    def test_non_primitive_serializable_value_getter(self):
        class NonPrimitiveSerializableObject(
                jsonobject.JsonSerializableObject):
            @jsonobject.jsonproperty
            def field_child_foo(self):
                return 'child_foo'

        class NonPrimitiveSerializableValueGetter(
                jsonobject.JsonSerializableObject):
            # OK if the non primitive value is JSON serializable.
            @jsonobject.jsonproperty
            def field_foo(self):
                return NonPrimitiveSerializableObject()

        assert (NonPrimitiveSerializableValueGetter().json() ==
                '{"field_foo": {"field_child_foo": "child_foo"}}')

    def test_getter_setter_deleter(self):
        class GetterSetterDeleter(jsonobject.JsonSerializableObject):
            def __init__(self, foo):
                self._foo = foo

            @jsonobject.jsonproperty
            def field_foo(self):
                return self._foo

            # Setters and deleters can be used just like the standard property.
            @field_foo.setter
            def field_foo(self, foo):
                self._foo = foo

            @field_foo.deleter
            def field_foo(self):
                del self._foo

        gsd = GetterSetterDeleter(123)
        assert gsd.field_foo == 123
        assert gsd.json() == '{"field_foo": 123}'
        gsd.field_foo = 456
        assert gsd.field_foo == 456
        assert gsd.json() == '{"field_foo": 456}'
        del gsd.field_foo
        with pytest.raises(AttributeError):
            assert gsd.field_foo

    def test_json_property(self):
        class SuccinctProperty(jsonobject.JsonSerializableObject):
            # This does the same thing as @jsonproperty getter and setter.
            field_foo = jsonobject.JsonProperty('field_foo')

        sp = SuccinctProperty()
        # The property defaults to None.
        assert sp.field_foo is None
        sp.field_foo = 123
        assert sp.field_foo == 123
        assert sp.json() == '{"field_foo": 123}'
        del sp.field_foo
        with pytest.raises(AttributeError):
            assert sp.field_foo

    def test_json_readonly_property(self):
        class ReadonlyProperty(jsonobject.JsonSerializableObject):
            def __init__(self, foo):
                self._foo = foo

            # This property export self._foo as a readonly property.
            foo = jsonobject.ReadonlyJsonProperty('field_foo', '_foo')

        rp = ReadonlyProperty(123)
        assert rp.foo == 123
        with pytest.raises(AttributeError):
            rp.foo = 456
        assert rp.json('{"field_foo": 123}')


def main():
    import doctest
    doctest.testmod(jsonobject)
    pytest.main(args=[__file__.replace('.pyc', '.py')])


if __name__ == '__main__':
    main()
