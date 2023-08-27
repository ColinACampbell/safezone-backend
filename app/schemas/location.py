from pydantic import BaseModel
from typing import Optional

class LocationBase(BaseModel) :
    name:str
    id:int
    lat:float
    lon:float

