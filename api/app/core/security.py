from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from fastapi import HTTPException

from app.core.config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM

#Model for the user and JWT payload
class User(BaseModel):
    username: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    '''Hash a plaintext password.'''
    return pwd_context.hash(password) #hash a plaintext password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    '''Verify a hashed password'''
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    '''JWT token creation'''
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    '''JWT token validation'''
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return User(username=username)
    except JWTError:
        raise credentials_exception