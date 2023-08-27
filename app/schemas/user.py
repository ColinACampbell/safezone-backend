from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel) :
    first_name:str
    last_name:str
    email:str

class UserCreate(UserBase) :
    password:str

class UserAuth(UserCreate) :
    first_name:Optional[str] = None
    last_name:Optional[str] = None
    email:str

class UserReturn(UserBase) :
    id:int
    token:Optional[str] = None


    
