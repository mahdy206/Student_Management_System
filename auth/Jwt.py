from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from App.Database import get_db
from App.Models.User import User
from App.Utils.Logger import logger
import os

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(data: dict) -> str:
    """Creates a signed JWT token with an expiration time."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decodes the JWT token and returns the authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        logger.warning(f"Token references non-existent user: {email}")
        raise credentials_exception

    logger.debug(f"Authenticated user: {user.email} (role={user.role})")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that only allows admin users through."""
    if current_user.role != "admin":
        logger.warning(f"Admin access denied for user: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user