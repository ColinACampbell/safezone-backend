from app.database.models.group import Confidant, Group
from app.database.models.medical_record import MedicalRecord
from app.schemas.medical_record import MedicalRecordBase, MedicalRecordCreate, MedicalRecordReturn
from fastapi import APIRouter, Depends, HTTPException, status
from app.database.models.user import User
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.utils import user_utils

router = APIRouter()

def are_both_users_in_same_group(user_id:int, current_user_id: int, db:Session) :
    def lists_overlap(a, b):
        return bool(set(a) & set(b))
    # check if both users are in the same group
    confidant_membership: Confidant = db.query(Confidant).filter(Confidant.user == user_id).all()
    current_user_membership: Confidant = db.query(Confidant).filter(Confidant.user == current_user_id).all()
    confidant_groups = [x.group for x in confidant_membership ]
    current_user_groups = [x.group for x in current_user_membership ]

    if (lists_overlap(confidant_groups,current_user_groups)) :
        return True
    else:
        return False

@router.post("/", response_model=MedicalRecordReturn, tags=['medical-record'])
def create_medical_record(medical_record_create : MedicalRecordCreate, db : Session = Depends(get_db), current_user : User = Depends(get_current_user)):
    new_medical_record: MedicalRecord = MedicalRecord(user=current_user.id, title = medical_record_create.title, description = medical_record_create.description)
    db.add(new_medical_record)
    db.commit()
    db.flush()

    medical_record_return = MedicalRecordReturn(id=new_medical_record.id, user_id=current_user.id, 
                                                title = medical_record_create.title, 
                                                description = medical_record_create.description)
    
    return medical_record_return

@router.get("/", response_model=List[MedicalRecordReturn],  tags=['medical-record'])
def get_medical_records( db : Session = Depends(get_db), current_user : User = Depends(get_current_user)):
    
    medical_records : list[MedicalRecord] = db.query(MedicalRecord).filter(MedicalRecord.user == current_user.id).all()
    medical_records_return = []
    
    for record in medical_records :
        record_return = MedicalRecordReturn(id=record.id, user_id=current_user.id, 
                                                title = record.title, 
                                                description = record.description)
        
        medical_records_return.append(record_return)

    
    return medical_records_return

@router.get("/{user_id}", response_model=List[MedicalRecordReturn], tags=['medical-record'])
def get_medical_records_for_user( user_id: int, db : Session = Depends(get_db), current_user : User = Depends(get_current_user)):
    

    current_user_is_auth = are_both_users_in_same_group(user_id,current_user.id,db)

    if current_user_is_auth :
        medical_records : list[MedicalRecord] = db.query(MedicalRecord).filter(MedicalRecord.user == user_id).all()
        medical_records_return = []
        
        for record in medical_records :
            record_return = MedicalRecordReturn(id=record.id, user_id=current_user.id, 
                                                    title = record.title, 
                                                    description = record.description)
            
            medical_records_return.append(record_return)

        
        return medical_records_return
    else :
        raise HTTPException(
                status_code=401,  # status.HTTP_401_UNAUTHORIZED,
                detail="You do not have permission",
                headers={"WWW-Authenticate": "Bearer"},
            )