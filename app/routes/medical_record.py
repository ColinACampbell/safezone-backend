from app.database.models.medical_record import MedicalRecord
from app.schemas.medical_record import MedicalRecordBase, MedicalRecordCreate, MedicalRecordReturn
from fastapi import APIRouter, Depends, HTTPException, status
from app.database.models.user import User
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.utils import user_utils

router = APIRouter()

@router.post("/", response_model=MedicalRecordReturn)
def create_medical_record(medical_record_create : MedicalRecordCreate, db : Session = Depends(get_db), current_user : User = Depends(get_current_user)):
    new_medical_record: MedicalRecord = MedicalRecord(user=current_user.id, title = medical_record_create.title, description = medical_record_create.description)
    db.add(new_medical_record)
    db.commit()
    db.flush()

    medical_record_return = MedicalRecordReturn(id=new_medical_record.id, user_id=current_user.id, 
                                                title = medical_record_create.title, 
                                                description = medical_record_create.description)
    
    return medical_record_return

@router.get("/", response_model=List[MedicalRecordReturn])
def get_medical_records( db : Session = Depends(get_db), current_user : User = Depends(get_current_user)):
    
    medical_records : list[MedicalRecord] = db.query(MedicalRecord).filter(MedicalRecord.user == current_user.id).all()
    medical_records_return = []
    
    for record in medical_records :
        record_return = MedicalRecordReturn(id=record.id, user_id=current_user.id, 
                                                title = record.title, 
                                                description = record.description)
        
        medical_records_return.append(record_return)

    
    return medical_records_return