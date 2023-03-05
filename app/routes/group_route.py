from fastapi import APIRouter, Depends, HTTPException, status
from app.database.models.user import User
from app.schemas.group import GroupReturn, GroupBase, ConfidantReturn
from app.schemas.user import UserReturn
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.database.models.group import Group, Confidant
from app.utils import user_utils

router = APIRouter()

def get_confidants(group:Group, db: Session) :
    confidants: list[Confidant] = group.confidants
    confidants_rtn : list[ConfidantReturn] = []

    for confidant in confidants :
        db_user: User = db.query(User).filter(User.id == confidant.user).first()
        user_rtn : UserReturn = UserReturn(first_name=db_user.first_name, last_name=db_user.last_name, email=db_user.last_name, id=db_user.id)
        new_confidant : ConfidantReturn = ConfidantReturn(id=confidant.id, details=user_rtn)
        confidants_rtn.append(new_confidant)

    return confidants_rtn

@router.post("/", response_model=GroupReturn)
def create_group(group: GroupBase, db: Session = Depends(get_db), current_user:User = Depends(get_current_user)):
    exisiting_group = db.query(Group).filter(Group.name == group.name).first()
    if exisiting_group == None :
        db_group = Group(name=group.name, created_by = current_user.id)
        db.add(db_group)
        db.commit()
        db.refresh(db_group)

        grp_admin = Confidant(role="admin",group=db_group.id, user=current_user.id) # TODO: Put roles in an ENUM
        db.add(grp_admin)
        db.commit()
        db.refresh(grp_admin)

        print(db_group.confidants[0].user)
        grp_return = GroupReturn(name=db_group.name, id=db_group.id, created_by=db_group.created_by, confidants=get_confidants(group=db_group,db=db))
        return grp_return
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