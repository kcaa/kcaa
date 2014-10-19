#!/usr/bin/env python

import pytest

import model


class TestKCAAObject(object):

    def test_update_generation(self):
        obj = model.KCAAObject()
        assert obj.auto_generation
        assert obj.generation == 0
        obj.update('', None, None, None, False)
        assert obj.generation == 1
        obj.update('', None, None, None, False)
        assert obj.generation == 2

    def test_update_no_auto_generation(self):
        class NoAutoGenerationKCAAObject(model.KCAAObject):
            @property
            def auto_generation(self):
                return False

        obj = NoAutoGenerationKCAAObject()
        assert not obj.auto_generation
        assert obj.generation == 0
        obj.update('', None, None, None, False)
        assert obj.generation == 0


class Item(object):

    def __init__(self, id_, value=None):
        self._id = id_
        self._value = value

    @property
    def id(self):
        return self._id

    @property
    def value(self):
        return self._value

    def __cmp__(self, obj):
        if cmp(self._id, obj._id) != 0:
            return cmp(self._id, obj._id)
        return cmp(self._value, obj._value)

    def __repr__(self):
        return 'Item({}, {})'.format(repr(self._id), repr(self._value))


class TestModel(object):

    def test_merge_list_empty(self):
        old_list = [Item(0), Item(1), Item(2)]
        new_list = []
        assert model.merge_list(old_list, new_list) == old_list
        old_list = []
        new_list = [Item(0), Item(1), Item(2)]
        assert model.merge_list(old_list, new_list) == new_list

    def test_merge_list_extend(self):
        old_list = [Item(0), Item(1)]
        new_list = [Item(2), Item(3)]
        assert model.merge_list(old_list, new_list) == old_list + new_list

    def test_merge_list_rewrite(self):
        old_list = [Item(0, 'foo')]
        new_list = [Item(0, 'bar')]
        assert model.merge_list(old_list, new_list) == new_list

    def test_merge_list_partial_rewrite(self):
        old_list = [Item(0, 'foo'), Item(1, 'bar')]
        new_list = [Item(1, 'baz'), Item(2, 'qux')]
        assert (model.merge_list(old_list, new_list) ==
                [Item(0, 'foo'), Item(1, 'baz'), Item(2, 'qux')])

    def test_merge_list_interpolate(self):
        old_list = [Item(0, 'foo'), Item(3, 'qux')]
        new_list = [Item(1, 'bar'), Item(2, 'baz')]
        assert (model.merge_list(old_list, new_list) ==
                [Item(0, 'foo'), Item(1, 'bar'), Item(2, 'baz'),
                 Item(3, 'qux')])

    def test_merge_list_reverse_interpolate(self):
        old_list = [Item(1, 'bar'), Item(2, 'baz')]
        new_list = [Item(0, 'foo'), Item(3, 'qux')]
        assert (model.merge_list(old_list, new_list) ==
                [Item(0, 'foo'), Item(1, 'bar'), Item(2, 'baz'),
                 Item(3, 'qux')])


def main():
    import doctest
    doctest.testmod(model)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
