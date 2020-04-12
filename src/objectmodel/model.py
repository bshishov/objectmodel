import json
import sys

from typing import Any, List, Dict, TypeVar, Generic, Type, Union, Protocol

__all__ = ['Field', 'ObjectField', 'ListCollectionField', 'DictCollectionField',
           'DuplicateFieldDefinition', 'ObjectModelMeta', 'ObjectModel', 'JsonSerializableModel',
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

_T = TypeVar('_T')


class Field:
    __slots__ = 'name', 'default', 'required', 'allow_none', 'validator'

    def __init__(self,
                 name: str = NOT_PROVIDED,
                 default: _T = NOT_PROVIDED,
                 required: bool = False,
                 allow_none: bool = False,
                 validator=None):
        self.name = name
        self.default = default
        self.required = required
        self.allow_none = allow_none
        self.validator = validator
        if self.default is None and not self.allow_none:
            raise RuntimeError(f'Default is None but None is not allowed for '
                               f'field \'{self.name}\'. Check field settings')

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
        raise AttributeError(f'Field \'{self.name}\' of model \'{owner.__name__}\' is not set')

    def __set__(self, model_instance: 'ObjectModel', value: _T):
        assert isinstance(model_instance, ObjectModel)
        if value is None and not self.allow_none:
            raise AttributeError(f'Field \'{self.name}\' of model '
                                 f'\'{model_instance.__class__.__name__}\' cannot be None')
        model_instance.__state__[self.name] = value

    def __set_name__(self, owner, name):
        if self.name is NOT_PROVIDED:
            assert name and isinstance(name, str), 'String name must be specified'
            self.name = name

    def __delete__(self, model_instance):
        assert isinstance(model_instance, ObjectModel)
        del model_instance.__state__[self.name]

    def serialize(self, model_instance: 'ObjectModel') -> Any:
        return self.__get__(model_instance, model_instance.__class__)

    def deserialize(self, model_instance: 'ObjectModel', value):
        self.__set__(model_instance, value)

    def has_default(self) -> bool:
        return self.default is not NOT_PROVIDED

    def has_value(self, model_instance: 'ObjectModel'):
        return self.name in model_instance.__state__

    def validate(self, model_instance: 'ObjectModel', raise_on_error=False) -> bool:
        if self.validator:
            value = self.__get__(model_instance, model_instance.__class__)
            if not self.validator.validate(model_instance, self, value):
                if raise_on_error:
                    raise AttributeError(
                        f'Field {self.name} of model {model_instance.__class__.__name__} '
                        f'is not valid. Validator: {self.validator.__class__.__name__}. '
                        f'Got value: {value}')
                return False
        return True

    def clear(self, model_instance):
        self.__delete__(model_instance)

    def __repr__(self):
        return f'<Field(name={self.name})>'


class ProxyField(Field):
    def __init__(self, attr_name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._attr_name = attr_name

    def __get__(self, instance, owner):
        return getattr(instance, self._attr_name)

    def has_value(self, model_instance: 'ObjectModel'):
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

    def validate(self, model_instance: 'ObjectModel', raise_on_error=False) -> bool:
        base_validation_result = super().validate(model_instance, raise_on_error)
        if not base_validation_result:
            return base_validation_result
        value: ObjectModel = self.__get__(model_instance, model_instance.__class__)
        return value.validate(raise_on_error)


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
        for v in value:
            obj = self._resolve_item_type()()
            obj.deserialize(v)
            deserialized_list.append(obj)
        super().deserialize(instance, deserialized_list)

    def _resolve_item_type(self) -> Type['ObjectModel']:
        if issubclass(self._model, ObjectModel):
            return self._model
        elif isinstance(self._model, str):
            self._model = getattr(sys.modules[__name__], self._model)
            return self._model
        else:
            raise TypeError(f'Cant resolve model type: {self._model}')

    def validate(self, model_instance: 'ObjectModel', raise_on_error=False) -> bool:
        base_validation_result = super().validate(model_instance, raise_on_error)
        if not base_validation_result:
            return base_validation_result
        value: List[ObjectModel] = self.__get__(model_instance, model_instance.__class__)
        for item in value:
            if not item.validate(raise_on_error):
                return False
        return True


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

    def validate(self, model_instance: 'ObjectModel', raise_on_error=False) -> bool:
        base_validation_result = super().validate(model_instance, raise_on_error)
        if not base_validation_result:
            return base_validation_result
        value: Dict[Any, ObjectModel] = self.__get__(model_instance, model_instance.__class__)
        for item in value.values():
            if not item.validate(raise_on_error):
                return False
        return True


class DuplicateFieldDefinition(AttributeError):
    def __init__(self, field_name, class_name):
        super().__init__(f'Duplicate field definition found during {class_name} initialization, '
                         f'field: {field_name}')


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
    __slots__ = '__state__', '_dict_factory'

    # fields class attr is set during class construction in ObjectModelMeta.__new__
    __fields__: Dict[str, Field]

    def __init__(self, dict_factory: callable = dict, **kwargs):
        self.__state__ = {}
        self._dict_factory = dict_factory
        for attr_name, attr_value in kwargs.items():
            if attr_name not in self.__fields__:
                raise AttributeError(f'Unexpected argument: {attr_name}, '
                                     f'no such field in model {self.__class__.__name__}')
            setattr(self, attr_name, attr_value)

    def validate(self, raize=False) -> bool:
        for field in self.__fields__.values():
            if not field.validate(self, raize):
                return False
        return True

    def deserialize(self, data: Dict[str, Any]):
        for key, value in data.items():
            field = self.__fields__.get(key, None)
            if field:
                field.deserialize(self, value)

    def serialize(self) -> Dict[str, Any]:
        result = self._dict_factory()
        for field in self.__fields__.values():
            if field.has_default() or field.has_value(self):
                result[field.name] = field.serialize(self)
            else:
                if field.required:
                    raise KeyError(f'Field {field.name} of '
                                   f'model {self.__class__.__name__} '
                                   f'is required')
        return result

    # Aliases
    to_dict = serialize
    from_dict = deserialize

    def clear(self):
        for field in self.__fields__.values():
            field.clear(self)

    def __setstate__(self, state: Dict[str, Any]):
        self.deserialize(state)

    def __getstate__(self) -> Dict[str, Any]:
        return self.serialize()


class JsonSerializableModel(ObjectModel):
    def to_json(self) -> str:
        data = self.serialize()
        return json.dumps(data)

    def from_json(self, raw: str):
        data = json.loads(raw)
        self.deserialize(data)

    def from_json_file(self, file):
        data = json.load(file)
        self.deserialize(data)
