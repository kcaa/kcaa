#!/usr/bin/env python

import pytest

import model


class TestJsonSerializableObject(object):

    class OneGetter(model.JsonSerializableObject):

        @model.json_serialized_property
        def field_foo(self):
            return 'foo'

    def test_one_getter(self):
        getter = TestJsonSerializableObject.OneGetter()
        assert getter.json() == '{"field_foo": "foo"}'


def main():
    pytest.main(args=[__file__.replace('.pyc', '.py')])


if __name__ == '__main__':
    main()
