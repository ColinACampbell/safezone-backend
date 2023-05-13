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

        grp_return = GroupReturn(name=db_group.name, id=db_group.id, created_by=db_group.created_by, confidants=get_confidants(group=db_group,db=db))
        return grp_return
    else :
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This group already exists")

@router.get("/", response_model=List[GroupReturn])
def get_groups(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    groups : list[Group] = []

    # first select where the user is a confidant
    memberships : list[Confidant] = db.query(Confidant).filter(Confidant.user == current_user.id).all()
    # second get the groups for which the confidant belongs to and build a list
    for membership in memberships :
        db_group : Group = db.query(Group).filter(Group.id == membership.group).first()
        groups.append(db_group)

    groups_rtn : GroupReturn = []
    for db_group in groups:
        group_rtn = GroupReturn(id=db_group.id, name=db_group.name, confidants=get_confidants(db_group,db), created_by=db_group.created_by)
        groups_rtn.append(group_rtn)

    return groups_rtn[skip:limit + skip]


@router.get("/{group_id}", response_model=GroupReturn)
def read_group(group_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_group = db.query(Group).filter(Group.id == group_id).first()

    def get_confidant_id(confidant : ConfidantReturn) :
        return confidant.details.id

    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    else :
        grp_confidants = get_confidants(db_group,db)
        member_ids = list(map(get_confidant_id, grp_confidants))
        print(member_ids)
        if current_user.id in member_ids :
            group_rtn = GroupReturn(id=db_group.id, name=db_group.name, confidants=get_confidants(db_group,db), created_by=db_group.created_by)
            return group_rtn
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this group")



@router.delete("/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    db.delete(db_group)
    db.commit()
    return {"message": "Group deleted"}


@router.post("/{group_id}/restriction/{user_id}") 
def geo_restrict_user(group_id:int, user_id:int, db:Session = Depends(get_db)) :
    pass

@router.delete("/{group_id}/restriction/{user_id}") 
def delete_geo_restriction(group_id:int, user_id:int, db:Session = Depends(get_db)) :
    pass

@router.get("/{group_id}/restriction") 
def get_all_geo_restrictions(group_id:int, user_id:int, db:Session = Depends(get_db)) :
    pass