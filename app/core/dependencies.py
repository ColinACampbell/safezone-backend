from fastapi import Depends, HTTPException, status
from pydantic import ValidationError
from app.database import SessionLocal
from app.database.models.user import User
from app.utils import user_utils
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime
from jose import jwt


def get_db():
    """
    It creates a database connection and returns it to the caller
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    return get_user_from_token(db,token)

def get_user_from_token(db:Session, token:str) -> User :
    try:
        payload = user_utils.verify_token(token=token)
        # oken_data = TokenPayload(**payload)

        if datetime.fromtimestamp(payload['exp']) < datetime.now():
            raise HTTPException(
                status_code=401,  # status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except(jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=403,  # status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter_by(id=int(payload['sub'])).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find user",
        )

    return user