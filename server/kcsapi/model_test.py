#!/usr/bin/env python

import pytest

import model


class TestJsonSerializableObject(object):

    def test_default_getter(self):

        class DefaultGetter(model.JsonSerializableObject):
            # Can decorate without any arguments.
            @model.json_serialized_property
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
            # @model.json_serialized_property('FOO')
            @model.json_serialized_property(name='FOO')
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
            @model.json_serialized_property(store_if_null=False)
            def field_foo(self):
                return self.value

        assert NamedConservativeGetter('foo').json() == '{"field_foo": "foo"}'
        assert NamedConservativeGetter(None).json() == '{}'


def main():
    pytest.main(args=[__file__.replace('.pyc', '.py')])


if __name__ == '__main__':
    main()
