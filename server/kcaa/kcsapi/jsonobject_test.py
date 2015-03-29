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

    def test_not_exported_if_omittable(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            def __init__(self, value):
                self.value = value

            # If omittable is True, the property will not exported.
            # This is the default behavior if omitted.
            @jsonproperty(omittable=True)
            def foo(self):
                return self.value

        assert SomeObject('FOO').json() == '{"foo": "FOO"}'
        assert SomeObject('').json() == '{"foo": ""}'
        assert SomeObject(0).json() == '{"foo": 0}'
        assert SomeObject(None).json() == '{}'

    def test_exported_if_not_omittable(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            def __init__(self, value):
                self.value = value

            # If omittable is False, the property will always be exported.
            @jsonproperty(omittable=False)
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
        # Deletion is not supported.
        with pytest.raises(AttributeError):
            del s.foo

    def test_json_property_default(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            # default speficies the default value of the property.
            foo = jsonobject.JSONProperty('foo', default='FOO')

        s = SomeObject()
        assert s.foo == 'FOO'
        s.foo = 'BAR'
        assert s.foo == 'BAR'

    def test_json_property_non_reused_default_list(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            # List passed as the default value. This should not be reused over
            # object instances.
            foo = jsonobject.JSONProperty('foo', default=[])

        s = SomeObject()
        assert s.foo == []
        s.foo.append('FOO')
        assert s.foo == ['FOO']
        t = SomeObject()
        assert t.foo == []
        t.foo.append('BAR')
        assert t.foo == ['BAR']
        assert s.foo == ['FOO']

    def test_json_property_non_reused_default_list_consistency(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            foo = jsonobject.JSONProperty('foo', default=[])

        # The getter should return the same object regardless of the timing of
        # member access.
        s = SomeObject()
        foo_id = id(s.foo)
        foo_id_2 = id(s.foo)
        assert foo_id == foo_id_2

    def test_json_property_non_reused_default_dict(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            # Dict passed as the default value. This should not be reused over
            # object instances.
            foo = jsonobject.JSONProperty('foo', default={})

        s = SomeObject()
        assert s.foo == {}
        s.foo['bar'] = 'BAR'
        assert s.foo['bar'] == 'BAR'
        t = SomeObject()
        assert t.foo == {}
        t.foo['bar'] = 'BAZ'
        assert t.foo['bar'] == 'BAZ'
        assert s.foo['bar'] == 'BAR'

    def test_json_property_non_reused_default_object(self):
        class ChildObject(jsonobject.JSONSerializableObject):
            bar = jsonobject.JSONProperty('bar', default='BAR')

        class SomeObject(jsonobject.JSONSerializableObject):
            # Dict passed as the default value. This should not be reused over
            # object instances.
            foo = jsonobject.JSONProperty('foo', default=ChildObject())

        s = SomeObject()
        assert s.foo.bar == 'BAR'
        s.foo.bar = 'BAZ'
        assert s.foo.bar == 'BAZ'
        t = SomeObject()
        assert t.foo.bar == 'BAR'
        t.foo.bar = 'QUX'
        assert t.foo.bar == 'QUX'
        assert s.foo.bar == 'BAZ'

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

    def test_json_property_not_shared_between_instances(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            foo = jsonobject.JSONProperty('foo')

        s = SomeObject(foo='FOO')
        t = SomeObject(foo='BAR')
        assert s.foo == 'FOO'
        assert t.foo == 'BAR'

    def test_json_readonly_property(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            def __init__(self, foo):
                self._foo = foo

            # This property exports SomeObject._foo in a readonly manner.
            foo = jsonobject.ReadonlyJSONProperty('foo',
                                                  wrapped_variable='_foo')

        s = SomeObject('FOO')
        assert s.foo == 'FOO'
        # Client code cannot assign a value to s.foo.
        with pytest.raises(AttributeError):
            s.foo = 'BAR'
        assert s.json('{"foo": "FOO"}')

    def test_readonly_json_property_init(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            # If wrapped_variable is omitted, the property tries to wrap one
            # with a random unique name.
            foo = jsonobject.ReadonlyJSONProperty('foo',
                                                  wrapped_variable='_foo')
            # This is a class variable whose name conflicts with the wrapped
            # variable of foo.
            _foo = 'CLASS_FOO'

        # JSONSerializableObject constructor accepts key-value specifications
        # for ReadonlyJSONProperty too. It creates a private variable with the
        # name passed as the second argument (wrapped_variable).
        s = SomeObject(foo='FOO')
        assert s.foo == 'FOO'
        assert s._foo == 'FOO'
        # There is a class variable whose name conflicts with that.
        # JSONSerializableObject's constructor never overwrite the class
        # variable, but you may want to avoid these situations, as it looks
        # very weird. (Of course, that looks like a design flaw to begin with.)
        assert SomeObject._foo == 'CLASS_FOO'

    def test_readonly_json_property_default(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            foo = jsonobject.ReadonlyJSONProperty('foo', default='FOO')

        assert SomeObject().foo == 'FOO'
        assert SomeObject(foo='BAR').foo == 'BAR'

    def test_readonly_json_property_not_shared_between_instances(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            foo = jsonobject.ReadonlyJSONProperty('foo')

        s = SomeObject(foo='FOO')
        t = SomeObject(foo='BAR')
        assert s.foo == 'FOO'
        assert t.foo == 'BAR'

    def test_nested_jsonobject(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            a = jsonobject.JSONProperty('a', default='A')
            b = jsonobject.ReadonlyJSONProperty('b', default='B')

            @jsonproperty
            def c(self):
                return 'C'

        # You can create a nested class from another serializable object class.
        class AnotherObject(SomeObject):
            d = jsonobject.JSONProperty('d', default='D')
            e = jsonobject.ReadonlyJSONProperty('e', default='E')

            @jsonproperty
            def f(self):
                return 'F'

        s = SomeObject()
        assert s.json(sort_keys=True) == '{"a": "A", "b": "B", "c": "C"}'
        t = AnotherObject()
        assert t.json(sort_keys=True) == ('{"a": "A", "b": "B", "c": "C", '
                                          '"d": "D", "e": "E", "f": "F"}')
        # You can initialize superclass' properties as well.
        # Note that, however, properties created by @jsonproperty is not
        # initializable from this syntax.
        u = AnotherObject(a="AA", b="BB", d="DD", e="EE")
        assert u.json(sort_keys=True) == ('{"a": "AA", "b": "BB", "c": "C", '
                                          '"d": "DD", "e": "EE", "f": "F"}')

    def test_overriding_jsonobject(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            a = jsonobject.JSONProperty('a', default='A')
            b = jsonobject.JSONProperty('b', default='B')

            def update_a(self, value):
                self.a = value

        class AnotherObject(SomeObject):
            # You can override some properties exported by the superclass.
            a = jsonobject.JSONProperty('a', default='AA')

        s = SomeObject()
        assert s.json(sort_keys=True) == '{"a": "A", "b": "B"}'
        t = AnotherObject()
        assert t.json(sort_keys=True) == '{"a": "AA", "b": "B"}'
        t.update_a('AAA')
        assert t.json(sort_keys=True) == '{"a": "AAA", "b": "B"}'
        u = AnotherObject(a='AAAA', b='BBBB')
        assert u.json(sort_keys=True) == '{"a": "AAAA", "b": "BBBB"}'

    def test_value_type(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            a = jsonobject.JSONProperty('a', default='A', value_type=str)
            b = jsonobject.JSONProperty('b', default=123, value_type=int)
            c = jsonobject.JSONProperty('c', default='C')

        s = SomeObject()
        assert s.json(sort_keys=True) == '{"a": "A", "b": 123, "c": "C"}'
        # It's a value type violation when setting a value of different type.
        with pytest.raises(TypeError):
            s.a = 123
        with pytest.raises(TypeError):
            s.b = 'B'
        # c doesn't declare the value type: any arbitrary type is acceptable.
        s.c = 456
        assert s.json(sort_keys=True) == '{"a": "A", "b": 123, "c": 456}'

    def test_value_type_default(self):
        # It's also forbidden to have an incompatible default value.
        # Note that this check happens when a class is being defined.
        with pytest.raises(TypeError):
            class SomeObject(jsonobject.JSONSerializableObject):
                a = jsonobject.JSONProperty('a', default='A', value_type=int)

    def test_value_type_int_long(self):
        # It is allowed to assign an int to a field expecting a long.
        class SomeObject(jsonobject.JSONSerializableObject):
            a = jsonobject.JSONProperty('a', default=123, value_type=long)

        s = SomeObject()
        assert s.a == 123
        s.a = int(456)
        assert s.a == 456

    def test_value_type_readonly(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            a = jsonobject.ReadonlyJSONProperty('a', default='A',
                                                value_type=str)

        with pytest.raises(TypeError):
            SomeObject(a=123)

    def test_value_type_readonly_wrapped_variable(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            a = jsonobject.ReadonlyJSONProperty('a', value_type=str,
                                                wrapped_variable='_a')

        s = SomeObject(a=None)
        assert s._a is None
        s._a = 123
        # ReadonlyJSONProperty checks value type on read.
        with pytest.raises(TypeError):
            assert s.a == 123

    def test_value_type_readonly_default(self):
        with pytest.raises(TypeError):
            class SomeObject(jsonobject.JSONSerializableObject):
                a = jsonobject.JSONProperty('a', default='A', value_type=int)

    def test_element_type_list(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            a = jsonobject.JSONProperty('a', value_type=list, element_type=int)

        s = SomeObject(a=[1, 2, 3])
        with pytest.raises(TypeError):
            s.a = ['1', '2', '3']

    def test_element_type_tuple(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            a = jsonobject.JSONProperty('a', value_type=tuple,
                                        element_type=int)

        s = SomeObject(a=(1, 2, 3))
        with pytest.raises(TypeError):
            s.a = ('1', '2', '3')

    def test_element_type_dict(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            a = jsonobject.JSONProperty('a', value_type=dict, element_type=int)

        s = SomeObject(a={'a': 1, 'b': 2})
        assert s.a['a'] == 1
        assert s.a['b'] == 2
        with pytest.raises(TypeError):
            s.a = {'a': '1', 'b': '2'}

    def test_key_type_dict(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            a = jsonobject.JSONProperty('a', value_type=dict)

        s = SomeObject(a={'a': 1, 'b': 2})
        assert s.a['a'] == 1
        assert s.a['b'] == 2
        s.a = {u'a': 3, u'b': 4}
        assert s.a['a'] == 3
        assert s.a['b'] == 4
        with pytest.raises(TypeError):
            s.a = {1: 1, 2: 2}

    def test_parse_text(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            foo = jsonobject.JSONProperty('foo', u'FOO', value_type=unicode)
            bar = jsonobject.JSONProperty('bar', 0, value_type=int)

        s = SomeObject.parse_text('{"foo": "FOOFOO", "bar": 123}')
        assert s.foo == u'FOOFOO'
        assert s.bar == 123
        t = SomeObject.parse_text('{}')
        assert t.foo == u'FOO'
        assert t.bar == 0
        # Ill-formed JSON.
        with pytest.raises(ValueError):
            SomeObject.parse_text('{"foo": "FOO}')
        # Value type mismatch.
        with pytest.raises(TypeError):
            SomeObject.parse_text('{"foo": 123}')
        # Unknown field was found.
        with pytest.raises(AttributeError):
            SomeObject.parse_text('{"baz": 123}')
        # Unknown field was found, but ignored.
        u = SomeObject.parse_text('{"baz": 123}', _ignore_unknown=True)
        assert u.json(sort_keys=True) == '{"bar": 0, "foo": "FOO"}'

    def test_parse_overriding(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            foo = jsonobject.JSONProperty('foo', u'FOO', value_type=unicode)

        s = SomeObject.parse({'foo': u'FOOFOO'})
        assert s.foo == u'FOOFOO'
        t = SomeObject.parse({'foo': u'FOOFOO'}, foo=u'FOOFOOFOO')
        assert t.foo == u'FOOFOOFOO'

    def test_parse_nested(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            foo = jsonobject.JSONProperty('foo', 123, value_type=int)

        class AnotherObject(jsonobject.JSONSerializableObject):
            bar = jsonobject.JSONProperty('bar', value_type=SomeObject)

        s = AnotherObject.parse_text('{"bar": {"foo": 123}}')
        assert isinstance(s.bar, SomeObject)
        assert s.bar.foo == 123

    def test_parse_dict_int(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            foo = jsonobject.JSONProperty('foo', value_type=dict,
                                          element_type=int)

        s = SomeObject.parse_text('{"foo": {"a": 1, "b": 2}}')
        assert len(s.foo) == 2
        assert s.foo['a'] == 1
        assert s.foo['b'] == 2

    def test_parse_dict_long(self):
        # Element type declared as long, but it's acceptable to receive int
        # values. They are always safe to upcast.
        class SomeObject(jsonobject.JSONSerializableObject):
            foo = jsonobject.JSONProperty('foo', value_type=dict,
                                          element_type=long)

        s = SomeObject.parse_text('{"foo": {"a": 1, "b": 2}}')
        assert len(s.foo) == 2
        assert s.foo['a'] == 1
        assert s.foo['b'] == 2

    def test_parse_dict_object(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            foo = jsonobject.JSONProperty('foo', 123, value_type=int)

        class AnotherObject(jsonobject.JSONSerializableObject):
            bar = jsonobject.JSONProperty('bar', value_type=dict,
                                          element_type=SomeObject)

        s = AnotherObject.parse_text('{"bar": {"a": {"foo": 1}, '
                                     '"b": {"foo": 2}}}')
        assert len(s.bar) == 2
        assert isinstance(s.bar['a'], SomeObject)
        assert s.bar['a'].foo == 1
        assert isinstance(s.bar['b'], SomeObject)
        assert s.bar['b'].foo == 2

    def test_parse_list(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            foo = jsonobject.JSONProperty('foo', 123, value_type=int)

        class AnotherObject(jsonobject.JSONSerializableObject):
            bar = jsonobject.JSONProperty('bar', value_type=list,
                                          element_type=SomeObject)

        s = AnotherObject.parse_text('{"bar": [{"foo": 1}, {"foo": 2}]}')
        assert len(s.bar) == 2
        assert isinstance(s.bar[0], SomeObject)
        assert s.bar[0].foo == 1
        assert isinstance(s.bar[1], SomeObject)
        assert s.bar[1].foo == 2
        s.bar[0] = SomeObject(foo=3)
        assert s.bar[0].foo == 3

    def test_parse_tuple(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            foo = jsonobject.JSONProperty('foo', 123, value_type=int)

        class AnotherObject(jsonobject.JSONSerializableObject):
            bar = jsonobject.JSONProperty('bar', value_type=tuple,
                                          element_type=SomeObject)

        s = AnotherObject.parse_text('{"bar": [{"foo": 1}, {"foo": 2}]}')
        assert len(s.bar) == 2
        assert isinstance(s.bar[0], SomeObject)
        assert s.bar[0].foo == 1
        assert isinstance(s.bar[1], SomeObject)
        assert s.bar[1].foo == 2
        # Tuple should not allow mutation.
        with pytest.raises(TypeError):
            s.bar[0] = SomeObject(foo=3)

    def test_parse_different_name(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            # There may be a case where the property name in Python and JSON
            # differs, especially if the name is keywords like "or", "and" or
            # such.
            foo_ = jsonobject.JSONProperty('foo', value_type=int)

        s = SomeObject.parse_text('{"foo": 123}')
        assert s.foo_ == 123
        # From Python code, foo_ should be accessible as is.
        t = SomeObject(foo_=456)
        assert t.foo_ == 456

    def test_parse_swapped_name(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            # These name are swapped in JSON world. Such a situation should
            # never happen in reality, but in the specification, this is still
            # allowed.
            foo = jsonobject.JSONProperty('bar', value_type=int)
            bar = jsonobject.JSONProperty('foo', value_type=int)

        s = SomeObject.parse_text('{"foo": 123, "bar": 456}')
        assert s.foo == 456
        assert s.bar == 123
        # From Python code, they should be treated as is.
        t = SomeObject(foo=123, bar=456)
        assert t.foo == 123
        assert t.bar == 456

    def test_parse_field_in_parent(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            foo = jsonobject.JSONProperty('foo', value_type=int)

        class AnotherObject(SomeObject):
            bar = jsonobject.JSONProperty('bar', value_type=int)

        s = AnotherObject.parse_text('{"foo": 123, "bar": 456}')
        assert s.foo == 123
        assert s.bar == 456

    def test_instance_json_property(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            # Though it's not recommended for most use cases, JSON properties
            # can be created dynamically at instance creation time.
            # This is sometimes useful for dynamically importing unknown JSON
            # but do not abuse this. This is tricky. For readability, an
            # ordinary property should be explicitly declared at the class
            # level.
            def __init__(self, **kwargs):
                # Dynamically create a new type, because properties
                # (to be precise, descriptors) works if and only if owned by a
                # class object.
                cls = type('__{}_{}'.format(self.__class__.__name__, id(self)),
                           (jsonobject.JSONSerializableObject,),
                           dict(self.__class__.__dict__))
                # Change the class of this instance.
                self.__class__ = cls
                # Create properties dynamically and add to the dynamically
                # created class object. You may want to import not from kwargs,
                # and use JSON instead.
                for key, value in kwargs.iteritems():
                    if not hasattr(cls, key):
                        setattr(cls, key, jsonobject.JSONProperty(
                            key, default=value))
                # Set the value using JSONSerializableObject's constructor.
                super(cls, self).__init__(**kwargs)

            # Note that, this class level property will be present in the new
            # dynamically created class, because of self.__clas__.__dict__ is
            # passed to type() above.
            foo = jsonobject.JSONProperty('foo', default='FOO')

        s = SomeObject(bar='BAR')
        assert s.foo == 'FOO'
        assert s.bar == 'BAR'
        assert s.json(sort_keys=True) == '{"bar": "BAR", "foo": "FOO"}'
        # Confirm another instance won't suffer from any side effect.
        t = SomeObject(baz='BAZ')
        assert t.foo == 'FOO'
        assert t.baz == 'BAZ'
        assert t.json(sort_keys=True) == '{"baz": "BAZ", "foo": "FOO"}'

    def test_instance_json_property_shared_class(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            # Do not do something like this!
            # This is a bad example of a dynamic property, where I store a
            # property to a shared class object, which will produce a side
            # effect for other instances.
            def __init__(self, **kwargs):
                cls = self.__class__
                # Create properties dynamically and add to the shared class
                # object.
                for key, value in kwargs.iteritems():
                    if not hasattr(cls, key):
                        setattr(cls, key, jsonobject.JSONProperty(
                            key, default=value))
                # Set the value using JSONSerializableObject's constructor.
                super(cls, self).__init__(**kwargs)

            foo = jsonobject.JSONProperty('foo', default='FOO')

        s = SomeObject(bar='BAR')
        # This is expected...
        assert s.foo == 'FOO'
        assert s.bar == 'BAR'
        assert s.json(sort_keys=True) == '{"bar": "BAR", "foo": "FOO"}'
        # Also this is fine...
        t = SomeObject(baz='BAZ')
        assert t.foo == 'FOO'
        assert t.baz == 'BAZ'
        # But what is this?! Why do I have bar here though I don't define it
        # for t!
        assert t.bar == 'BAR'
        assert t.json(sort_keys=True) == ('{"bar": "BAR", "baz": "BAZ", '
                                          '"foo": "FOO"}')
        # That's why I put a property to the shared class object.
        # So, use a dynamic class object like what's in
        # test_instance_json_property. (But to begin with, avoid using a
        # dynamic property as much as possible.)

    def test_instance_json_property_simple(self):
        class SomeObject(jsonobject.JSONSerializableObject):
            # This is a bit simple version of dynamic property creation.
            # This way the class definition is much simpler...
            def __init__(self, **kwargs):
                super(SomeObject, self).__init__(**kwargs)
                # bar is a dynamically created property.
                self.bar = jsonobject.JSONProperty('bar', default='BAR')

            foo = jsonobject.JSONProperty('foo', default='FOO')

        s = SomeObject()
        assert s.foo == 'FOO'
        # However, you cannot manipulate bar naturally.
        # You would call __get__(), __set__() to directly talk with this
        # property (descriptor) object.
        assert s.bar.__get__(s) == 'BAR'
        # Serializing to JSON is still straightforward.
        assert s.json(sort_keys=True) == '{"bar": "BAR", "foo": "FOO"}'


class TestDynamicJSONSerializableObject(object):

    def test_invalid(self):
        with pytest.raises(TypeError):
            jsonobject.parse_text('null')
        with pytest.raises(TypeError):
            jsonobject.parse_text('"foo"')
        with pytest.raises(TypeError):
            jsonobject.parse_text('123')
        with pytest.raises(TypeError):
            jsonobject.parse_text('["foo", "bar"]')
        with pytest.raises(ValueError):
            # Looks like a map, but corrupted.
            jsonobject.parse_text('{"foo": "bar}')

    def test_readwrite_omittable(self):
        s = jsonobject.parse_text('{"foo": "FOO", "bar": "BAR"}',
                                  readonly=False, omittable=True)
        assert s.foo == u'FOO'
        assert s.bar == u'BAR'
        assert s.json(sort_keys=True) == '{"bar": "BAR", "foo": "FOO"}'
        s.foo = u'FOOFOO'
        s.bar = None
        # Note that every property is omittable.
        assert s.json(sort_keys=True) == '{"foo": "FOOFOO"}'

    def test_readwrite_not_omittable(self):
        s = jsonobject.parse_text('{"foo": "FOO", "bar": "BAR"}',
                                  readonly=False, omittable=False)
        assert s.json(sort_keys=True) == '{"bar": "BAR", "foo": "FOO"}'
        s.foo = u'FOOFOO'
        s.bar = None
        # No property is omittable.
        assert s.json(sort_keys=True) == '{"bar": null, "foo": "FOOFOO"}'

    def test_readonly_omittable(self):
        s = jsonobject.parse_text('{"foo": "FOO", "bar": null}',
                                  readonly=True, omittable=True)
        assert s.foo == u'FOO'
        assert s.bar is None
        with pytest.raises(AttributeError):
            s.foo = u'FOOFOO'
        with pytest.raises(AttributeError):
            s.bar = u'BARBAR'
        # Every property is omittable, so bar should be omitted even though it
        # appeared in the input.
        assert s.json(sort_keys=True) == '{"foo": "FOO"}'

    def test_readonly_not_omittable(self):
        s = jsonobject.parse_text('{"foo": "FOO", "bar": null}',
                                  readonly=True, omittable=False)
        assert s.foo == u'FOO'
        assert s.bar is None
        # No property is omittable.
        assert s.json(sort_keys=True) == '{"bar": null, "foo": "FOO"}'

    def test_nested_map(self):
        # Nested map should create a nested JSONSerializableObject.
        s = jsonobject.parse_text('{"foo": "FOO", "bar": {"baz": "BAZ"}}')
        assert s.foo == u'FOO'
        assert s.bar.baz == u'BAZ'

    def test_list(self):
        # List should create a list of JSONSerializableObject.
        s = jsonobject.parse_text('{"foo": [{"bar": 1}, {"bar": 2}]}')
        assert len(s.foo) == 2
        assert s.foo[0].bar == 1
        assert s.foo[1].bar == 2

    def test_value_overriding(self):
        obj = {'foo': 'FOO', 'bar': 'BAR'}
        s = jsonobject.parse(obj)
        assert s.foo == u'FOO'
        assert s.bar == u'BAR'
        assert s.json(sort_keys=True) == '{"bar": "BAR", "foo": "FOO"}'
        # With parse, you can override some values.
        t = jsonobject.parse(obj, bar='BARBAR')
        assert t.foo == u'FOO'
        assert t.bar == u'BARBAR'
        assert t.json(sort_keys=True) == '{"bar": "BARBAR", "foo": "FOO"}'
        # If no value available in the input object, a new property will be
        # created (no exception thrown).
        u = jsonobject.parse(obj, baz='BAZ')
        assert u.foo == u'FOO'
        assert u.bar == u'BAR'
        assert u.baz == u'BAZ'
        assert u.json(sort_keys=True) == ('{"bar": "BAR", "baz": "BAZ", '
                                          '"foo": "FOO"}')


def main():
    import doctest
    doctest.testmod(jsonobject)
    import sys
    sys.exit(pytest.main(args=[__file__.replace('.pyc', '.py')]))


if __name__ == '__main__':
    main()
