# objectmodel
Python typed object model for schema creation and validation

A bit unpythonic object definition, but sometimes things should be strict and typed :)
Ideal for protocols and schemas.

Objects populated by ObjectModel class guarantee to match the desired state and fully serializable at any time.

# Installation

This library is still in a development state, so please dont use it right away - the API might change at any time
```
pip install -i https://test.pypi.org/simple/ objectmodel
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
* More tests!
* More examples
* Auto-deployment to PyPI

# Examples
```lang=python
from typing import List, Optional, Any
import time

from objectmodel import *


class User(ObjectModel):
    name: str = Field(required=True)
    created: float = Field(default=time.time)
    friends: List['User'] = ListCollectionField(item_model='User', default=list, required=False)
    any_object: Optional[Any] = Field(required=False, allow_none=True)

user1 = User('First')
user2 = User('Second')

user3 = User('Third')
user3.friends.append(user1)
user3.friends.append(user2)

print(user3.serialize())
# {'created': 1586718388.8557358,
# 'friends': [{'created': 1586718388.8557358, 'friends': [], 'name': 'First'},
#             {'created': 1586718388.8557358, 'friends': [], 'name': 'Second'}],
# 'name': 'Third'}
```
