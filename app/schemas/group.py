from pydantic import BaseModel
from typing import List, Optional

from app.schemas.user import UserReturn


class ConfidantBase(BaseModel) :
    role: str

class ConfidantCreate(ConfidantBase) :
    user_id:int
    group_id:int

class ConfidantReturn(BaseModel) :
    id:int
    details: UserReturn
    role: Optional[str]

# Also used to create
class GroupBase(BaseModel):
    name: str

class GroupReturn(GroupBase):
    id: int
    confidants : list[ConfidantReturn]
    created_by: int

class GeoRestrictionCreate(BaseModel) :
    user_id : int
    group_id : int
    latitude : float
    longitude : float
    radius : float