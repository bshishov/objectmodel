from typing import Any, Dict

from objectmodel.base import FieldABC, ObjectModelABC


__all__ = [
    'ObjectModel',
    'ObjectModelMeta'
]


def is_instance_or_subclass(val, klass) -> bool:
    try:
        return issubclass(val, klass)
    except TypeError:
        return isinstance(val, klass)


def _iter_fields(attrs: Dict[str, Any], field_class: type = FieldABC):
    for attr_name, attr in attrs.items():
        if is_instance_or_subclass(attr, field_class):
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


class ObjectModel(ObjectModelABC, metaclass=ObjectModelMeta):
    DICT_FACTORY = dict

    __slots__ = '__state__'

    # fields class attr is set during class construction in ObjectModelMeta.__new__
    __fields__: Dict[str, FieldABC]

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
