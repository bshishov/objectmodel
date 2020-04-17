import unittest
from unittest.mock import MagicMock

from objectmodel import *


class ObjectTests(unittest.TestCase):
    def test_empty_instance(self):
        class A(ObjectModel):
            pass

        obj = A()
        self.assertDictEqual(obj.__fields__, {})
        self.assertDictEqual(obj.__state__, {})

    def test_field_binding(self):
        class A(ObjectModel):
            foo = Field()

        instance = A()
        self.assertTrue('foo' in A.__fields__)
        self.assertTrue('foo' in instance.__fields__)
        self.assertTrue('foo' not in instance.__state__)

    def test_field_binding_with_custom_name(self):
        class A(ObjectModel):
            foo = Field(name='data key')

        instance = A()
        self.assertTrue('foo' in A.__fields__)
        self.assertTrue('foo' in instance.__fields__)
        self.assertTrue('data key' not in instance.__state__)

    def test_set_field(self):
        class A(ObjectModel):
            foo = Field(required=False)

        instance = A()
        value = object()
        instance.foo = value
        self.assertEqual(instance.__state__['foo'], value)
        self.assertEqual(instance.foo, value)

    def test_access_not_set_attribute_raises(self):
        class A(ObjectModel):
            foo = Field()

        instance = A()

        with self.assertRaises(AttributeError):
            value = instance.foo

    def test_default_value(self):
        value = object()

        class A(ObjectModel):
            foo = Field(default=value)

        instance = A()
        self.assertTrue('foo' not in instance.__state__)
        assert instance.foo == value
        assert 'foo' in instance.__state__

    def test_callable_default(self):
        value = object()
        factory = MagicMock(return_value=value)

        class A(ObjectModel):
            foo = Field(default=factory)

        instance = A()

        assert 'foo' not in instance.__state__
        assert instance.foo == value
        factory.assert_called_with()
        assert 'foo' in instance.__state__

    def test_field_inheritance(self):
        class A(ObjectModel):
            foo = Field()

        class B(A):
            bar = Field()

        assert len(B.__fields__) == 2
        assert 'foo' in B.__fields__
        assert 'bar' in B.__fields__
        assert 'foo' in A.__fields__
        assert 'bar' not in A.__fields__

    def test_kwargs_init(self):
        class A(ObjectModel):
            foo = Field()
            bar = Field()

        obj = A(foo=42, bar='hello')
        assert obj.foo == 42
        assert obj.bar == 'hello'

    def test_not_filled_required_field_raises(self):
        class A(ObjectModel):
            foo = Field(required=True)

        with self.assertRaises(FieldValueRequiredError):
            A()
