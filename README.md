# objectmodel
Python typed object model for schema creation and validation


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
