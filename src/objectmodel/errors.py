from typing import Optional, Any

from objectmodel.base import ObjectModelABC, FieldABC


__all__ = [
    'FieldValidationError',
    'FieldValueRequiredError',
    'DuplicateFieldDefinitionError'
]


class FieldValidationError(AttributeError):
    """ Field validation error """

    def __init__(self, instance: Optional[ObjectModelABC], field: FieldABC, value: Any, message: str):
        super().__init__(f'Invalid value {value} for field {field!r} of {instance!r}: {message}')


class FieldValueRequiredError(AttributeError):
    """ Field is required but not set """

    def __init__(self, instance: ObjectModelABC, field: FieldABC):
        super().__init__(f'Field {field!r} of {instance!r} is not set')


class DuplicateFieldDefinitionError(AttributeError):
    """ A field with this name is already present in model """
    def __init__(self, field_name: str, class_name: str):
        super().__init__(f'Duplicate field definition found during {class_name} initialization, '
                         f'field: {field_name}')
