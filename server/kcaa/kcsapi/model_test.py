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


class MockKCAAJournalObject(model.KCAAJournalObject):

    def __init__(self, monitored_objects, *args, **kwargs):
        self._monitored_objects = monitored_objects
        super(MockKCAAJournalObject, self).__init__(*args, **kwargs)
        self.called = 0
        self.api_names = []
        self.object_args = {}

    @property
    def monitored_objects(self):
        return self._monitored_objects

    def update(self, api_names, **object_args):
        self.called += 1
        self.api_names = api_names
        self.object_args = object_args


class TestKCAAJournalObject(object):

    def test_update_no_monitored_objects(self):
        journal = MockKCAAJournalObject(['SomeObject'])
        assert journal.called == 0
        journal._update([], {})
        assert journal.called == 0

    def test_update_single(self):
        journal = MockKCAAJournalObject(['SomeObject'])
        assert journal.called == 0
        # SomeObject updated; update() should be called.
        api_names = ['/api/foo']
        objects = {'SomeObject': model.KCAAObject(generation=1)}
        journal._update(api_names, objects)
        assert journal.called == 1
        assert journal.api_names == api_names
        assert journal.object_args == {'some_object': objects['SomeObject']}
        # Next _update() with no object updates.
        journal._update(api_names, objects)
        assert journal.called == 1
        # SomeObject updated again.
        objects['SomeObject'].generation += 1
        journal._update(api_names, objects)
        assert journal.called == 2
        assert journal.api_names == api_names
        assert journal.object_args == {'some_object': objects['SomeObject']}

    def test_update_double(self):
        journal = MockKCAAJournalObject(['SomeObject', 'AnotherObject'])
        assert journal.called == 0
        # SomeObject and AnotherObject updated; update() should be called.
        api_names = ['/api/foo', '/api/bar']
        objects = {'SomeObject': model.KCAAObject(generation=1),
                   'AnotherObject': model.KCAAObject(generation=1)}
        journal._update(api_names, objects)
        assert journal.called == 1
        assert journal.api_names == api_names
        assert journal.object_args == {
            'some_object': objects['SomeObject'],
            'another_object': objects['AnotherObject']}
        # Next _update() with no object updates.
        journal._update(api_names, objects)
        assert journal.called == 1
        # SomeObject updated again.
        objects['SomeObject'].generation += 1
        journal._update(api_names, objects)
        assert journal.called == 2
        assert journal.api_names == api_names
        assert journal.object_args == {
            'some_object': objects['SomeObject'],
            'another_object': objects['AnotherObject']}
        # Next _update() with no object updates.
        journal._update(api_names, objects)
        assert journal.called == 2
        # AnotherObject updated again.
        objects['AnotherObject'].generation += 1
        journal._update(api_names, objects)
        assert journal.called == 3
        assert journal.api_names == api_names
        assert journal.object_args == {
            'some_object': objects['SomeObject'],
            'another_object': objects['AnotherObject']}


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

    def test_translate_object_name_empty(self):
        assert model.translate_object_name('') == ''

    def test_translate_object_name_one(self):
        assert model.translate_object_name('Ship') == 'ship'
        assert model.translate_object_name('Fleet') == 'fleet'
        assert model.translate_object_name('Battle') == 'battle'

    def test_translate_object_name_two(self):
        assert model.translate_object_name('ShipList') == 'ship_list'
        assert model.translate_object_name('PlayerInfo') == 'player_info'
        assert model.translate_object_name('RepairDock') == 'repair_dock'

    def test_translate_object_name_three(self):
        assert (model.translate_object_name('SomeComplexName') ==
                'some_complex_name')
        assert (model.translate_object_name('SCN') ==
                's_c_n')

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
