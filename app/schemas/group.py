from pydantic import BaseModel
from typing import List, Optional


class GroupBase(BaseModel):
    name: str
    members: List[str]

class GroupCreate(GroupBase):
    pass

class GroupAuth(BaseModel):
    username: str
    password: str

class GroupReturn(GroupBase):
    id: int