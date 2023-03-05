from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.user import UserCreate, UserReturn, UserAuth
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.database.models.user import User
from app.utils import user_utils


router = APIRouter()

@router.post("/",response_model=UserReturn)
def signup_user(user_create:UserCreate, db: Session = Depends(get_db)) :
    exisiting_user = db.query(User).filter(User.email == user_create.email).first()
    if exisiting_user == None :
        new_user = User(email=user_create.email, first_name=user_create.first_name, last_name=user_create.last_name, password  = user_utils.get_hashed_password(user_create.password))
        db.add(new_user)
        db.commit()
        user_return = UserReturn(id=new_user.id, email=new_user.email, first_name=new_user.first_name, last_name=new_user.last_name, token=user_utils.create_access_token(str(new_user.id)))
        return user_return
    else :
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This user already exists")
    

@router.post("/auth",response_model=UserReturn)
def signup_user(user_create:UserAuth, db: Session = Depends(get_db)) :
    exisiting_user = db.query(User).filter(User.email == user_create.email).first()
    if exisiting_user == None :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This user does not exist")
    else :
        if (user_utils.verify_password(user_create.password,exisiting_user.password)) :
            user_return = UserReturn(id=exisiting_user.id, email=exisiting_user.email, first_name=exisiting_user.first_name, last_name=exisiting_user.last_name, token=user_utils.create_access_token(str(exisiting_user.id)))
            return user_return
        else :
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Credentials are incorrect")