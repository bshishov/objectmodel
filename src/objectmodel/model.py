import sys

from typing import Any, List, Dict, TypeVar, Type, Union, Optional, Callable
from objectmodel.errors import *

__all__ = ['Field', 'ObjectField', 'ListCollectionField', 'DictCollectionField',
           'ObjectModelMeta', 'ObjectModel', 'ProxyField']


class _NotProvided:
    def __bool__(self):
        return False

    def __copy__(self):
        return self

    def __deepcopy__(self, _):
        return self

    def __repr__(self):
        return "<objectmodel.NOT_PROVIDED>"


NOT_PROVIDED = _NotProvided()

_T = TypeVar('_T')


class Field:
    __slots__ = 'name', 'default', 'required', 'allow_none', 'validator'

    def __init__(self,
                 name: str = NOT_PROVIDED,
                 default: Union[Callable[[], _T], _T] = NOT_PROVIDED,
                 required: bool = False,
                 allow_none: bool = False,
                 validator: Optional[Callable[[Optional['ObjectModel'], 'Field', Any], None]] = None):
        self.name = name
        self.default = default
        self.required = required
        self.allow_none = allow_none
        self.validator = validator

        # Defaults also should be validated!
        if not callable(default):
            self.validate(None, default)

    def __get__(self, model_instance: 'ObjectModel', owner: Type['ObjectModel']) -> _T:
        assert isinstance(model_instance, ObjectModel)
        try:
            return model_instance.__state__[self.name]
        except KeyError:
            if self.default is not NOT_PROVIDED:
                default = self.default
                if callable(default):
                    default = default()
                self.__set__(model_instance, default)
                return default
        raise FieldValueRequiredError(model_instance, self)

    def __set__(self, model_instance: 'ObjectModel', value: _T):
        assert isinstance(model_instance, ObjectModel)
        self.validate(model_instance, value)
        model_instance.__state__[self.name] = value

    def __set_name__(self, owner, name):
        if self.name is NOT_PROVIDED:
            assert name and isinstance(name, str), 'String name must be specified'
            self.name = name

    def __delete__(self, model_instance):
        assert isinstance(model_instance, ObjectModel)
        if self.required:
            raise FieldValueRequiredError(model_instance, self)
        del model_instance.__state__[self.name]

    def serialize(self, model_instance: 'ObjectModel') -> Any:
        return self.__get__(model_instance, model_instance.__class__)

    def deserialize(self, model_instance: 'ObjectModel', value):
        self.__set__(model_instance, value)

    def has_default(self) -> bool:
        return self.default is not NOT_PROVIDED

    def has_value(self, model_instance: 'ObjectModel'):
        return self.name in model_instance.__state__

    def can_provide_value(self, model_instance: 'ObjectModel'):
        return self.default is not NOT_PROVIDED or self.name in model_instance.__state__

    def validate(self, model_instance: Optional['ObjectModel'], value: _T):
        if value is None and not self.allow_none:
            raise FieldValidationError(model_instance, self, value,
                                       'Cannot be None (allow_none=False)')
        if self.validator:
            value = self.__get__(model_instance, model_instance.__class__)
            self.validator(model_instance, self, value)

    def clear(self, model_instance):
        self.__delete__(model_instance)

    def __repr__(self):
        return '{}(name={!r}, default={!r}, required={!r}, allow_none={!r}, validator={!r})'\
            .format(
                self.__class__.__name__,
                self.name,
                self.default,
                self.required,
                self.allow_none,
                self.validator
            )


class ProxyField(Field):
    def __init__(self, attr_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._attr_name = attr_name

    def __get__(self, instance, owner):
        return getattr(instance, self._attr_name)

    def has_value(self, model_instance: 'ObjectModel') -> bool:
        return True


class ObjectField(Field):
    __slots__ = '_model'

    def __init__(self, name: str, model: type, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        assert issubclass(model, ObjectModel)
        self._model = model

    def serialize(self, model_instance: 'ObjectModel') -> Any:
        value = super().serialize(model_instance)
        if value is not None:
            return value.serialize()
        return None

    def deserialize(self, instance: 'ObjectModel', value):
        if value is not None:
            obj = self._model()
            obj.deserialize(value)
            super().deserialize(instance, obj)

    def validate(self, model_instance: 'ObjectModel', value):
        super().validate(model_instance, value)
        if not self.allow_none and value is not None:
            if not isinstance(value, ObjectModel):
                raise FieldValidationError(model_instance, self, value, f'Value should be of type: \'ObjectModel\'')
            value.validate()


class ListCollectionField(Field):
    __slots__ = '_model'

    def __init__(self, item_model: Union[str, Type['ObjectModel']], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model = item_model

    def serialize(self, model_instance: 'ObjectModel') -> Any:
        value = super().serialize(model_instance)
        return [v.serialize() for v in value]

    def deserialize(self, instance: 'ObjectModel', value):
        deserialized_list = []
        item_cls = self._resolve_item_type()
        for v in value:
            obj = item_cls()
            obj.deserialize(v)
            deserialized_list.append(obj)
        super().deserialize(instance, deserialized_list)

    def _resolve_item_type(self) -> Type['ObjectModel']:
        if issubclass(self._model, ObjectModel):
            return self._model
        elif isinstance(self._model, str):
            self._model = getattr(sys.modules[__name__], self._model)
            return self._model
        raise TypeError(f'Cant resolve item model type: {self._model}')

    def validate(self, model_instance: 'ObjectModel', value):
        super().validate(model_instance, value)
        if not self.allow_none and value is not None:
            if not isinstance(value, list):
                raise FieldValidationError(model_instance, self, value,
                                           'Value should be of type: List[ObjectModel]')
            for item in value:
                if not isinstance(item, ObjectModel):
                    raise FieldValidationError(model_instance, self, value,
                                               f'List item {item!r} '
                                               f'should be of type: \'ObjectModel\'')
                item.validate()


class DictCollectionField(Field):
    __slots__ = '_model', '_dict_factory'

    def __init__(self, name: str, item_model: type, dict_factory: callable = dict,
                 *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        assert issubclass(item_model, ObjectModel)
        self._model = item_model
        self._dict_factory = dict_factory

    def serialize(self, model_instance: 'ObjectModel') -> Any:
        value = super().serialize(model_instance)
        return {k: v.serialize() for k, v in value.items()}

    def deserialize(self, instance: 'ObjectModel', value):
        deserialized_dict = self._dict_factory()
        for k, v in value.items():
            obj = self._model()
            obj.deserialize(v)
            deserialized_dict[k] = obj
        super().deserialize(instance, deserialized_dict)

    def validate(self, model_instance: 'ObjectModel', value: Any):
        super().validate(model_instance, value)
        if not isinstance(value, dict):
            raise FieldValidationError(model_instance, self, value,
                                       'Value should be of type Dict[ObjectModel]')
        for item in value.values():
            item.validate()


def is_instance_or_subclass(val, klass) -> bool:
    try:
        return issubclass(val, klass)
    except TypeError:
        return isinstance(val, klass)


def _iter_fields(attrs: Dict[str, Any], field_class: type=Field):
    for attr_name, attr in attrs.items():
        if is_instance_or_subclass(attr, field_class) or attr_name.endswith('Field'):
            yield attr_name, attr


class ObjectModelMeta(type):
    FIELDS_ATTR = '__fields__'

    def __new__(mcs, name, bases, attrs):

        cls_fields = dict(_iter_fields(attrs))

        # TODO: clear fields from actual instance? and override __getattr__?
        """for field_name in cls_fields:
            del attrs[field_name]"""

        cls = super().__new__(mcs, name, bases, attrs)

        # TODO: Use MRO instead of iteration over base classes?
        for base in bases:
            base_attrs = getattr(base, '__fields__', base.__dict__)
            for field_name, field in _iter_fields(base_attrs):
                cls_fields[field_name] = field

        cls.__fields__ = cls_fields
        return cls


class ObjectModel(metaclass=ObjectModelMeta):
    DICT_FACTORY = dict

    __slots__ = '__state__'

    # fields class attr is set during class construction in ObjectModelMeta.__new__
    __fields__: Dict[str, Field]

    def __init__(self, **kwargs):
        self.__state__ = {}
        for attr_name, attr_value in kwargs.items():
            if attr_name not in self.__fields__:
                raise AttributeError(f'Unexpected argument: {attr_name}, '
                                     f'no such field in model {self.__class__.__name__}')
            setattr(self, attr_name, attr_value)

        # TODO: Fix double validation (first one happens in the settattr)
        self.validate()

    def validate(self):
        for field in self.__fields__.values():
            if field.has_value(self) or field.required:
                value = field.__get__(self, self.__class__)
                field.validate(self, value)

    def deserialize(self, data: Dict[str, Any]):
        for key, value in data.items():
            try:
                field = self.__fields__[key]
                field.deserialize(self, value)
            except KeyError:
                # We've received some additional info that does not correspond to a field
                pass

    def serialize(self) -> Dict[str, Any]:
        return self.DICT_FACTORY(
            (field.name, field.serialize(self))
            for field in self.__fields__.values()
            if field.can_provide_value(self)
        )

    def clear(self):
        for field in self.__fields__.values():
            field.clear(self)

    def __setstate__(self, state: Dict[str, Any]):
        self.deserialize(state)

    def __getstate__(self) -> Dict[str, Any]:
        return self.serialize()

    def __repr__(self):
        return '{}({})'.format(
            self.__class__.__name__,
            ', '.join(
                f'{name}={val!r}'
                for name, val in self.__state__.items()
            )
        )
