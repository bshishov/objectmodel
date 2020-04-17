from __future__ import annotations

from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from objectmodel.model import ObjectModel, Field
    from objectmodel.errors import FieldValidationError


Validator = Callable[[ObjectModel, Field, Any], None]


class FieldValidator:
    def __call__(self, instance: ObjectModel, field: Field, value: Any):
        raise NotImplementedError()


class OfType(FieldValidator):
    def __init__(self, typ, allow_none=False):
        self.typ = typ
        self.can_be_null = allow_none

    def __call__(self, instance: ObjectModel, field: Field, value: Any):
        if value is None:
            return self.can_be_null
        return isinstance(value, self.typ)


class NotEmptyString(FieldValidator):
    def __call__(self, instance: ObjectModel, field: Field, value: Any):
        if not isinstance(value, str) or not value:
            raise FieldValidationError(instance, field, value, 'Value should be a not-empty string')


class Numeric(FieldValidator):
    def __init__(self, allow_float=True, allow_none=False):
        self.allow_float = allow_float
        self.allow_none = allow_none

    def __call__(self, instance: ObjectModel, field: Field, value: Any):
        if value is None:
            return self.allow_none
        if isinstance(value, float) and not self.allow_float:
            return False
        return isinstance(value, (float, int))


class PositiveNumeric(Numeric):
    def __call__(self, instance: ObjectModel, field: Field, value: Any):
        super()(instance, field, value)
        return value >= 0


class MoreThanOrEqual(FieldValidator):
    def __init__(self, n):
        self.n = n

    def __call__(self, instance: ObjectModel, field: Field, value: Any):
        return value >= self.n


class ItemsOfType(FieldValidator):
    def __init__(self, typ):
        self.typ = typ

    def __call__(self, instance: ObjectModel, field: Field, value: Any):
        for item in value:
            if not isinstance(item, self.typ):
                return False
        return True


class ValidItems(FieldValidator):
    def __init__(self, *item_validators: Validator):
        self.item_validators = item_validators

    def __call__(self, instance: ObjectModel, field: Field, value: Any):
        for i, item in enumerate(value):
            for validator in self.item_validators:
                validator(instance, field, item)
        return True


class NotEmptyList(FieldValidator):
    def __call__(self, instance: ObjectModel, field: Field, value: Any):
        if not isinstance(value, list):
            return False
        return len(value) > 0


class MaxLen(FieldValidator):
    def __init__(self, max_len: int):
        self.max_len = max_len

    def __call__(self, instance: ObjectModel, field: Field, value: Any):
        return len(value) <= self.max_len


class ChainValidator(FieldValidator):
    def __init__(self, *validators: FieldValidator):
        self.validators = validators

    def __call__(self, instance: ObjectModel, field: Field, value: Any):
        for v in self.validators:
            v(instance, field, value)


class ValueIn(FieldValidator):
    def __init__(self, *args):
        if len(args) == 1:
            args = args[0]
        self.options = set(args)

    def __call__(self, instance: ObjectModel, field: Field, value: Any):
        return value in self.options


is_not_empty_string = NotEmptyString()
is_not_empty_string_of_max_len = (lambda x: ChainValidator(is_not_empty_string, MaxLen(x)))
is_numeric = Numeric()
is_integer = Numeric(allow_float=False)
is_positive_numeric = PositiveNumeric()
is_positive_integer = PositiveNumeric(allow_float=False)
is_bool = OfType(bool)
is_of_type = OfType
is_list_of = (lambda typ: ChainValidator(OfType(list), ItemsOfType(typ)))
is_not_empty_list = NotEmptyList()
is_not_empty_list_of = (lambda typ: ChainValidator(is_not_empty_list, ItemsOfType(typ)))
value_in = ValueIn
