from typing import Any, Type, Optional, Dict, TypeVar


__all__ = ['FieldABC', 'ObjectModelABC']


T = TypeVar('T')


class FieldABC:
    name: str
    required: bool

    def __get__(self, instance: 'ObjectModelABC', owner: Type['ObjectModelABC']) -> T:
        raise NotImplementedError

    def __set__(self, instance: 'ObjectModelABC', value: T):
        raise NotImplementedError

    def __set_name__(self, owner, name):
        raise NotImplementedError

    def __delete__(self, instance):
        raise NotImplementedError

    def serialize(self, instance: 'ObjectModelABC') -> Any:
        raise NotImplementedError

    def deserialize(self, instance: 'ObjectModelABC', value):
        raise NotImplementedError

    def has_default(self) -> bool:
        raise NotImplementedError

    def has_value(self, instance: 'ObjectModelABC'):
        raise NotImplementedError

    def can_provide_value(self, instance: 'ObjectModelABC'):
        raise NotImplementedError

    def validate(self, instance: Optional['ObjectModelABC'], value: T):
        raise NotImplementedError

    def clear(self, instance):
        raise NotImplementedError


class ObjectModelABC:
    __state__: Dict[str, Any]

    def serialize(self) -> Dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'ObjectModelABC':
        raise NotImplementedError

    def validate(self):
        raise NotImplementedError

