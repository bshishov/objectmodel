from objectmodel import ObjectModel

from typing import List, Optional, Any
import time
from uuid import uuid4

from objectmodel import *


def generate_id():
    return str(uuid4())[:8]


class User(ObjectModel):
    id = Field(required=True, default=generate_id)
    name: str = Field(required=True)
    created: float = Field(default=time.time)
    friends: List['User'] = ListCollectionField(item_model='User', default=list, required=False)
    any_object: Optional[Any] = Field(required=False, allow_none=True)


class User2:
    name: str


user1 = User(name='First')
user2 = User(name='Second')
user3 = User(name='Third')
user3.friends.append(user1)
user3.friends.append(user2)

print(user3.serialize())
# {'id': '89db1010', 'name': 'Third', 'created': 1586978465.466756, 'friends': [
#   {'id': '020354ce', 'name': 'First', 'created': 1586978465.466756, 'friends': []},
#   {'id': '9c64af3c', 'name': 'Second', 'created': 1586978465.466756, 'friends': []}
# ]}
