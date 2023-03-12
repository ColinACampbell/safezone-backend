from pydantic import BaseModel
from typing import List, Optional

from app.schemas.user import UserReturn


class ConfidantBase(BaseModel) :
    role: str

class ConfidantReturn(BaseModel) :
    id:int
    details: UserReturn

# Also used to create
class GroupBase(BaseModel):
    name: str

class GroupReturn(GroupBase):
    id: int
    confidants : list[ConfidantReturn]
    created_by: int
