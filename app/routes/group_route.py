from app.routes.medical_record import are_both_users_in_same_group
from fastapi import APIRouter, Depends, HTTPException, status
from app.database.models.user import User
from app.schemas.group import ConfidantCreate, GeoRestrictionBase, GeoRestrictionCreate, GroupReturn, GroupBase, ConfidantReturn
from app.schemas.user import UserReturn
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.dependencies import get_db, get_current_user
from app.database.models.group import GeoRestriction, Group, Confidant
from app.utils import user_utils

router = APIRouter()

def get_confidants(group:Group, db: Session) -> list[ConfidantReturn] :
    confidants: list[Confidant] = group.confidants
    confidants_rtn : list[ConfidantReturn] = []

    for confidant in confidants :
        db_user: User = db.query(User).filter(User.id == confidant.user).first()
        user_rtn : UserReturn = UserReturn(first_name=db_user.first_name, last_name=db_user.last_name, email=db_user.last_name, id=db_user.id)
        new_confidant : ConfidantReturn = ConfidantReturn(id=confidant.id, details=user_rtn, role=confidant.role)
        confidants_rtn.append(new_confidant)

    return confidants_rtn

# TODO: Write code to catch error if user does not exists
@router.post("/{groupId}/confidants", response_model=GroupReturn, tags=['group'])
def add_confidant(confidant_create:ConfidantCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing_confidant = db.query(Confidant).filter(Confidant.user == confidant_create.user_id, Confidant.group == confidant_create.group_id).first()
    if existing_confidant == None :
        # get the group they are adding for
        group : Group = db.query(Group).filter(Group.id == confidant_create.group_id).first()

        # check if they are in the group and have admin permission
        confidants = get_confidants(group=group,db=db);
        current_user_is_admin = False
        for confidant_user in confidants :
            print(confidant_user.role)
            if confidant_user.details.id == current_user.id and confidant_user.role == "admin" : # TODO: Convert to variable
                current_user_is_admin = True
        

        if (current_user_is_admin) :
            new_confidant = Confidant(user=confidant_create.user_id, group = confidant_create.group_id, role = confidant_create.role)
            db.add(new_confidant)
            db.commit()

            confidant_user_details:User = db.query(User).filter(User.id == confidant_create.user_id).first()
            
            grp_return = GroupReturn(name=group.name, id=group.id, created_by=group.created_by, confidants=get_confidants(group=group,db=db))
            return grp_return
        else :
            return HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail="You are not a guardian")
    else:
        return HTTPException(status_code = status.HTTP_409_CONFLICT)

@router.post("/", response_model=GroupReturn, tags=['group'])
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

@router.get("/", response_model=List[GroupReturn], tags=['group'])
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


@router.get("/{group_id}", response_model=GroupReturn, tags=['group'])
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



@router.delete("/{group_id}", tags=['group'])
def delete_group(group_id: int, db: Session = Depends(get_db)):
    db_group = db.query(Group).filter(Group.id == group_id).first()
    if db_group is None:
        raise HTTPException(status_code=404, detail="Group not found")
    db.delete(db_group)
    db.commit()
    return {"message": "Group deleted"}


@router.post("/{group_id}/restriction", tags=['group']) 
def geo_restrict_user(restriction: GeoRestrictionCreate, current_user:User = Depends(get_current_user), db:Session = Depends(get_db)) :
    group:Group = db.query(Group).filter(Group.id == restriction.group_id).first() 
    
    # check if the person doing the restriction is in the group, and is an admin
    currentUserIsAuthorized = False
    for confidant in group.confidants :
        if confidant.user == current_user.id :
            if confidant.role == "admin" :
                currentUserIsAuthorized = True

    if currentUserIsAuthorized :
        # now check if the user being added is in the group
        isAddedUserAuthorized = False
        for confidant in group.confidants :
            if confidant.user == restriction.user_id :
                isAddedUserAuthorized = True
        
        if (isAddedUserAuthorized) :
            # restrict the user 
            georestriction = GeoRestriction(user=restriction.user_id, group=restriction.group_id, latitude=restriction.latitude, longitude=restriction.longitude, radius=restriction.radius, from_time = restriction.from_time, to_time = restriction.to_time)
            db.add(georestriction)
            db.commit()
            return restriction
        else : 
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to make this request")
    else :
        # throw error 
        pass

@router.get("/{group_id}/restriction/{user_id}", response_model=list[GeoRestrictionBase], tags=['geofence','group']) 
def get_user_geo_restriction(group_id:int, user_id:int, current_user: User = Depends(get_current_user), db:Session = Depends(get_db)) :
    is_current_user_auth = are_both_users_in_same_group(user_id,current_user.id,db)
    confidant_geo_restrictions : list[GeoRestriction] = db.query(GeoRestriction).filter(GeoRestriction.group == group_id, GeoRestriction.user == user_id).all()
    if(is_current_user_auth) :
        geo_restriction_response : list[GeoRestrictionBase] = []
        for restriction in confidant_geo_restrictions :
            restriction_response = GeoRestrictionBase(user_id = restriction.user,
                group_id = restriction.group,
                latitude = restriction.latitude,
                longitude = restriction.longitude,
                radius = restriction.radius,
                from_time = restriction.from_time,
                to_time = restriction.to_time)
            geo_restriction_response.append(restriction_response)
        return geo_restriction_response
    else :
        raise HTTPException(
                status_code=401,  # status.HTTP_401_UNAUTHORIZED,
                detail="You do not have permission",
                headers={"WWW-Authenticate": "Bearer"},
            )

# TODO : Implement
@router.get("/{group_id}/restriction", tags=['group']) 
def get_all_geo_restrictions(group_id:int, user_id:int, db:Session = Depends(get_db)) :
    pass