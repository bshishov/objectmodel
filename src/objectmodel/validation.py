from typing import Any

from objectmodel.model import ObjectModel, Field


class FieldValidator:
    def validate(self, instance: ObjectModel, field: Field, value: Any) -> bool:
        raise NotImplementedError()


class OfType(FieldValidator):
    def __init__(self, typ, allow_none=False):
        self.typ = typ
        self.can_be_null = allow_none

    def validate(self, instance: ObjectModel, field: Field, value: Any) -> bool:
        if value is None:
            return self.can_be_null
        return isinstance(value, self.typ)


class NotEmptyString(FieldValidator):
    def validate(self, instance: ObjectModel, field: Field, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        if not value:
            return False
        return True


class Numeric(FieldValidator):
    def __init__(self, allow_float=True, allow_none=False):
        self.allow_float = allow_float
        self.allow_none = allow_none

    def validate(self, instance: ObjectModel, field: Field, value: Any) -> bool:
        if value is None:
            return self.allow_none
        if isinstance(value, float) and not self.allow_float:
            return False
        return isinstance(value, (float, int))


class PositiveNumeric(Numeric):
    def validate(self, instance: ObjectModel, field: Field, value: Any) -> bool:
        is_valid_numeric = super().validate(instance, field, value)
        if not is_valid_numeric:
            return False
        return value >= 0


class MoreThanOrEqual(FieldValidator):
    def __init__(self, n):
        self.n = n

    def validate(self, instance: ObjectModel, field: Field, value: Any) -> bool:
        return value >= self.n


class ItemsOfType(FieldValidator):
    def __init__(self, typ):
        self.typ = typ

    def validate(self, instance: ObjectModel, field: Field, value: Any) -> bool:
        for item in value:
            if not isinstance(item, self.typ):
                return False
        return True


class ValidItems(FieldValidator):
    def __init__(self, *item_validators: FieldValidator):
        self.item_validators = item_validators

    def validate(self, instance: ObjectModel, field: Field, value: Any) -> bool:
        for i, item in enumerate(value):
            for validator in self.item_validators:
                if not validator.validate(instance, field, item):
                    return False
        return True


class NotEmptyList(FieldValidator):
    def validate(self, instance: ObjectModel, field: Field, value: Any) -> bool:
        if not isinstance(value, list):
            return False
        return len(value) > 0


class MaxLen(FieldValidator):
    def __init__(self, max_len: int):
        self.max_len = max_len

    def validate(self, instance: ObjectModel, field: Field, value: Any) -> bool:
        return len(value) <= self.max_len


class ChainValidator(FieldValidator):
    def __init__(self, *validators: FieldValidator):
        self.validators = validators

    def validate(self, instance: ObjectModel, field: Field, value: Any) -> bool:
        for v in self.validators:
            if not v.validate(instance, field, value):
                return False
        return True


class ValueIn(FieldValidator):
    def __init__(self, *args):
        if len(args) == 1:
            args = args[0]
        self.options = set(args)

    def validate(self, instance: ObjectModel, field: Field, value: Any) -> bool:
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
