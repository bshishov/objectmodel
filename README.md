# objectmodel
Python typed object model for schema creation and validation

A bit unpythonic object definition, but sometimes things should be strict and typed :)
Ideal for protocols and schemas.

Objects populated by ObjectModel class guarantee to match the desired state and fully serializable at any time.

# Installation

This library is still in a development state, so please dont use it right away - the API might change at any time
```
pip install objectmodel
```


# TODO

* Performance benchmarks (ObjectModel vs plain object, namedtuple, dict)
* `__state__: Dict[str, Any]` vs dynamically populated `__slots__`
* Better validation and state ensurance
* Strict collections (`ObjectModelList` and `ObjectModelDict`)?
  * Separate key and value validation for collections
* Better field API
  * Predefined fields (`StringField`, `IntField`, `FloatField`)
* Proxy fields:
   * `MethodField` or `ComputedField`
* Readonly fields
* More tests!
* More examples
* Auto-deployment to PyPI
