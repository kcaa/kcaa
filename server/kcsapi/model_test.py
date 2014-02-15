#!/usr/bin/env python

import pytest

import model


class TestJsonSerializableObject(object):

    def test_default_getter(self):

        class DefaultGetter(model.JsonSerializableObject):
            # Can decorate without any arguments.
            @model.jsonproperty
            def field_foo(self):
                return 'foo'

        g = DefaultGetter()
        # field_foo can be used as a normal getter.
        assert g.field_foo == 'foo'
        # And is automatically exported.
        assert g.json() == '{"field_foo": "foo"}'

    def test_named_getter(self):
        class NamedGetter(model.JsonSerializableObject):
            # This field is exported as "FOO".
            # Note that parameters should be named; you can't do this way:
            # @model.jsonproperty('FOO')
            @model.jsonproperty(name='FOO')
            def field_foo(self):
                return 'foo'

        g = NamedGetter()
        assert g.field_foo == 'foo'
        assert g.json() == '{"FOO": "foo"}'

    def test_named_conservative_getter(self):
        class NamedConservativeGetter(model.JsonSerializableObject):
            def __init__(self, value):
                self.value = value

            # If you prefer, it's possible not to export if the value is null.
            # (In python, if the value is None.)
            @model.jsonproperty(store_if_null=False)
            def field_foo(self):
                return self.value

        assert NamedConservativeGetter('foo').json() == '{"field_foo": "foo"}'
        assert NamedConservativeGetter(None).json() == '{}'

    def test_named_aggressive_getter(self):
        class NamedAggressiveGetter(model.JsonSerializableObject):
            def __init__(self, value):
                self.value = value

            # By default, a null value is exported.
            @model.jsonproperty()
            def field_foo(self):
                return self.value

        assert NamedAggressiveGetter('foo').json() == '{"field_foo": "foo"}'
        assert NamedAggressiveGetter(None).json() == '{"field_foo": null}'

    def test_non_primitive_value_getter(self):
        class NonPrimitiveObject(object):
            pass

        class NonPrimitiveValueGetter(model.JsonSerializableObject):
            # The getter cannot return a non primitive value.
            @model.jsonproperty
            def field_foo(self):
                return NonPrimitiveObject()

        with pytest.raises(TypeError):
            NonPrimitiveValueGetter().json()

    def test_non_primitive_serializable_value_getter(self):
        class NonPrimitiveSerializableObject(model.JsonSerializableObject):
            @model.jsonproperty
            def field_child_foo(self):
                return 'child_foo'

        class NonPrimitiveSerializableValueGetter(
                model.JsonSerializableObject):
            # OK if the non primitive value is JSON serializable.
            @model.jsonproperty
            def field_foo(self):
                return NonPrimitiveSerializableObject()

        assert (NonPrimitiveSerializableValueGetter().json() ==
                '{"field_foo": {"field_child_foo": "child_foo"}}')

    def test_getter_setter_deleter(self):
        class GetterSetterDeleter(model.JsonSerializableObject):
            def __init__(self, foo):
                self._foo = foo

            @model.jsonproperty
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


def main():
    pytest.main(args=[__file__.replace('.pyc', '.py')])


if __name__ == '__main__':
    main()
