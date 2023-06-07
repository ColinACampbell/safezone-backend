from pydantic import BaseModel
from typing import Optional

class MedicalRecordBase(BaseModel) :
    title: str
    description: str

class MedicalRecordCreate(MedicalRecordBase):
    pass

class MedicalRecordReturn(MedicalRecordBase):
    id: int
    user_id: int