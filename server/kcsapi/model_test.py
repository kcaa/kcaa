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

        assert DefaultGetter().json() == '{"field_foo": "foo"}'

    def test_named_getter(self):
        class NamedGetter(model.JsonSerializableObject):

            # Parameters should be named.
            @model.json_serialized_property(name='FOO')
            def field_foo(self):
                return 'foo'

        assert NamedGetter().json() == '{"FOO": "foo"}'

    def test_named_conservative_getter(self):
        class NamedConservativeGetter(model.JsonSerializableObject):

            def __init__(self, value):
                self.value = value

            # Parameters should be named.
            @model.json_serialized_property(store_if_null=False)
            def field_foo(self):
                return self.value

        assert NamedConservativeGetter('foo').json() == '{"field_foo": "foo"}'
        assert NamedConservativeGetter(None).json() == '{}'


def main():
    pytest.main(args=[__file__.replace('.pyc', '.py')])


if __name__ == '__main__':
    main()
