from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.group import GroupCreate, GroupReturn, GroupAuth, GroupBase
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.database.models.group import Group
from app.utils import user_utils

router = APIRouter()

@router.post("/groups", response_model=GroupReturn)
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    exisiting_group = db.query(Group).filter(Group.name == group.name).first()
    if exisiting_group == None :
        db_group = Group(name=group.name, members=group.members)
        db.add(db_group)
        db.commit()
        db.refresh(db_group)
        return db_group
    else :
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This group already exists")

@router.get("/groups", response_model=List[GroupReturn])
def read_groups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    groups = db.query(Group).offset(skip).limit(limit).all()
    return groups


@router.get("/groups/{group_id}", response_model=GroupReturn)
def read_group(group_id: int, db: Session = Depends(get_db)):
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    return db_group


@router.delete("/groups/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    db.delete(db_group)
    db.commit()
    return {"message": "Group deleted"}