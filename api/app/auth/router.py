"""Endpoints for user registration and login."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import models
from app.auth.schemas import Token, UserCreate, UserLogin
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.swagger_docs import login_docs, registration_docs

router = APIRouter(tags=["Auth"])


def get_user(db: Session, username: str):
    """Retrieves the user from the database based on the username."""
    return db.query(models.User).filter(models.User.username == username).first()


@router.post("/registration", **registration_docs)
def register(user: UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(models.User).filter(or_(models.User.username == user.username, models.User.email == user.email)).first()

    #Check if user with the same email and username is already exists
    if existing_user:
        if existing_user.username == user.username:
            raise HTTPException(status_code=400, detail="Username already exists")
        if existing_user.email == user.email:
            raise HTTPException(status_code=400, detail="Email already exists")

    #Create a new user
    new_user = models.User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        username=user.username,
        password_hash=get_password_hash(user.password)  #Save a hashed password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User successfully registered", "email": new_user.email, "user_name": new_user.username}



@router.post("/login", response_model=Token, **login_docs)
def login_for_access_token(
        form_data: UserLogin, db: Session = Depends(get_db)):

    user = get_user(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    #Create access token
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}
