"""FastAPI dependencies shared by every endpoint that requires a logged-in user."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

from app.auth.models import User
from app.core.database import DbSession
from app.core.security import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DbSession) -> User:
    """Validates the JWT token and returns the currently logged-in user.

    If the token is not valid or the user does not exist, it raises an HTTPException.
    """
    user_data = verify_token(token)

    result = await db.execute(select(User).where(User.username == user_data.username))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


# Short name for endpoint parameters: `current_user: CurrentUser`
CurrentUser = Annotated[User, Depends(get_current_user)]
