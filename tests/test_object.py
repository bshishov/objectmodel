import pytest

from objectmodel import *


def test_empty_instance():
    class A(ObjectModel):
        pass

    obj = A()
    assert obj.__fields__ == {}
    assert obj.__state__ == {}


def test_field_binding():
    class A(ObjectModel):
        foo = Field()

    instance = A()
    assert 'foo' in A.__fields__
    assert 'foo' in instance.__fields__
    assert 'foo' not in instance.__state__


def test_field_binding_with_custom_name():
    class A(ObjectModel):
        foo = Field(name='data key')

    instance = A()
    assert 'foo' in A.__fields__
    assert 'foo' in instance.__fields__
    assert 'data key' not in instance.__state__


def test_set_field():
    class A(ObjectModel):
        foo = Field(required=False)

    instance = A()
    value = object()
    instance.foo = value
    assert instance.__state__['foo'] == value
    assert instance.foo == value


def test_access_not_set_attribute_raises():
    class A(ObjectModel):
        foo = Field()

    instance = A()

    with pytest.raises(AttributeError):
        value = instance.foo


def test_default_value():
    value = object()

    class A(ObjectModel):
        foo = Field(default=value)

    instance = A()
    assert 'foo' not in instance.__state__
    assert instance.foo == value
    assert 'foo' in instance.__state__


def test_callable_default():
    value = object()
    called = False

    def factory():
        nonlocal called
        called = True
        return value

    class A(ObjectModel):
        foo = Field(default=factory)

    instance = A()

    assert 'foo' not in instance.__state__
    assert instance.foo == value
    assert called
    assert 'foo' in instance.__state__


def test_field_inheritance():
    class A(ObjectModel):
        foo = Field()

    class B(A):
        bar = Field()

    assert len(B.__fields__) == 2
    assert 'foo' in B.__fields__
    assert 'bar' in B.__fields__
    assert 'foo' in A.__fields__
    assert 'bar' not in A.__fields__


def test_kwargs_init():
    class A(ObjectModel):
        foo = Field()
        bar = Field()

    obj = A(foo=42, bar='hello')
    assert obj.foo == 42
    assert obj.bar == 'hello'


def test_not_filled_required_field_raises():
    class A(ObjectModel):
        foo = Field(required=True)

    with pytest.raises(FieldValueRequiredError):
        A()
