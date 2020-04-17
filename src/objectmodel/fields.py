from __future__ import annotations

import sys

from typing import Any, TypeVar, Type, Union, Optional, Callable

from objectmodel.base import ObjectModelABC, FieldABC
from objectmodel.errors import FieldValidationError, FieldValueRequiredError


__all__ = [
    'NOT_PROVIDED',
    'Field',
    'ObjectField',
    'ListCollectionField',
    'DictCollectionField',
    'ProxyField']


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

T = TypeVar('T')


class Field(FieldABC):
    __slots__ = 'name', 'default', 'required', 'allow_none', 'validator'

    def __init__(self,
                 name: str = NOT_PROVIDED,
                 default: Union[Callable[[], T], T] = NOT_PROVIDED,
                 required: bool = False,
                 allow_none: bool = False,
                 validator: Optional[
                     Callable[[Optional[ObjectModelABC], FieldABC, Any], None]
                 ] = None):
        self.name = name
        self.default = default
        self.required = required
        self.allow_none = allow_none
        self.validator = validator

        # Defaults also should be validated!
        if not callable(default):
            self.validate(None, default)

    def __get__(self, instance: ObjectModelABC, owner: Type[ObjectModelABC]) -> T:
        assert isinstance(instance, ObjectModelABC)
        try:
            return instance.__state__[self.name]
        except KeyError:
            if self.default is not NOT_PROVIDED:
                default = self.default
                if callable(default):
                    default = default()
                self.__set__(instance, default)
                return default
        raise FieldValueRequiredError(instance, self)

    def __set__(self, instance: ObjectModelABC, value: T):
        assert isinstance(instance, ObjectModelABC)
        self.validate(instance, value)
        instance.__state__[self.name] = value

    def __set_name__(self, owner, name):
        if self.name is NOT_PROVIDED:
            assert name and isinstance(name, str), 'String name must be specified'
            self.name = name

    def __delete__(self, instance):
        assert isinstance(instance, ObjectModelABC)
        if self.required:
            raise FieldValueRequiredError(instance, self)
        del instance.__state__[self.name]

    def serialize(self, instance: ObjectModelABC) -> Any:
        return self.__get__(instance, instance.__class__)

    def deserialize(self, instance: ObjectModelABC, value):
        self.__set__(instance, value)

    def has_default(self) -> bool:
        return self.default is not NOT_PROVIDED

    def has_value(self, instance: ObjectModelABC):
        return self.name in instance.__state__

    def can_provide_value(self, instance: ObjectModelABC):
        return self.default is not NOT_PROVIDED or self.name in instance.__state__

    def validate(self, model_instance: Optional[ObjectModelABC], value: T):
        if value is None and not self.allow_none:
            raise FieldValidationError(model_instance, self, value,
                                       'Cannot be None (allow_none=False)')
        if self.validator:
            value = self.__get__(model_instance, model_instance.__class__)
            self.validator(model_instance, self, value)

    def clear(self, instance):
        self.__delete__(instance)

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

    def has_value(self, instance: ObjectModelABC) -> bool:
        return True


class ObjectField(Field):
    __slots__ = '_model'

    def __init__(self, name: str, model: type, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        assert issubclass(model, ObjectModelABC)
        self._model = model

    def serialize(self, instance: ObjectModelABC) -> Any:
        value = super().serialize(instance)
        if value is not None:
            return value.serialize()
        return None

    def deserialize(self, instance: ObjectModelABC, value):
        if value is not None:
            obj = self._model()
            obj.deserialize(value)
            super().deserialize(instance, obj)

    def validate(self, model_instance: ObjectModelABC, value):
        super().validate(model_instance, value)
        if not self.allow_none and value is not None:
            if not isinstance(value, ObjectModelABC):
                raise FieldValidationError(model_instance, self, value,
                                           f'Value should be of type: \'ObjectModel\'')
            value.validate()


class ListCollectionField(Field):
    __slots__ = '_model'

    def __init__(self, item_model: Union[str, Type[ObjectModelABC]], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._model = item_model

    def serialize(self, instance: ObjectModelABC) -> Any:
        value = super().serialize(instance)
        return [v.serialize() for v in value]

    def deserialize(self, instance: ObjectModelABC, value):
        deserialized_list = []
        item_cls = self._resolve_item_type()
        for v in value:
            obj = item_cls()
            obj.deserialize(v)
            deserialized_list.append(obj)
        super().deserialize(instance, deserialized_list)

    def _resolve_item_type(self) -> Type[ObjectModelABC]:
        if issubclass(self._model, ObjectModelABC):
            return self._model
        elif isinstance(self._model, str):
            self._model = getattr(sys.modules[__name__], self._model)
            return self._model
        raise TypeError(f'Cant resolve item model type: {self._model}')

    def validate(self, model_instance: ObjectModelABC, value):
        super().validate(model_instance, value)
        if not self.allow_none and value is not None:
            if not isinstance(value, list):
                raise FieldValidationError(model_instance, self, value,
                                           'Value should be of type: List[ObjectModel]')
            for item in value:
                if not isinstance(item, ObjectModelABC):
                    raise FieldValidationError(model_instance, self, value,
                                               f'List item {item!r} '
                                               f'should be of type: \'ObjectModel\'')
                item.validate()


class DictCollectionField(Field):
    __slots__ = '_model', '_dict_factory'

    def __init__(self, name: str, item_model: type, dict_factory: callable = dict,
                 *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        assert issubclass(item_model, ObjectModelABC)
        self._model = item_model
        self._dict_factory = dict_factory

    def serialize(self, instance: ObjectModelABC) -> Any:
        value = super().serialize(instance)
        return {k: v.serialize() for k, v in value.items()}

    def deserialize(self, instance: ObjectModelABC, value):
        deserialized_dict = self._dict_factory()
        for k, v in value.items():
            obj = self._model()
            obj.deserialize(v)
            deserialized_dict[k] = obj
        super().deserialize(instance, deserialized_dict)

    def validate(self, model_instance: ObjectModelABC, value: Any):
        super().validate(model_instance, value)
        if not isinstance(value, dict):
            raise FieldValidationError(model_instance, self, value,
                                       'Value should be of type Dict[ObjectModel]')
        for item in value.values():
            item.validate()
