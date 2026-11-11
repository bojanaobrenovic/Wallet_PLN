"""Pydantic models (request/response bodies) for authentication."""

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Data required to register a new user."""

    first_name: str
    last_name: str
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    """Credentials sent to the login endpoint."""

    username: str
    password: str


class Token(BaseModel):
    """Access token returned after a successful login."""

    access_token: str
    token_type: str
