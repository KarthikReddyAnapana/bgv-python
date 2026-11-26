from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import func
from sqlmodel import Session, select

from .config import settings
from .database import get_session
from .models import User

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Missing credentials go through ApiError so auth errors use the same JSON envelope as other errors.
_bearer = HTTPBearer(auto_error=False)


class ApiError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message


def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return _pwd.verify(password, hashed)


def create_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": user.email,
        "userId": user.id,
        "role": user.role,
        "organizationId": user.organization_id,
        "candidateId": user.candidate_id,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(milliseconds=settings.jwt_expiration_ms)).timestamp()),
    }
    return jwt.encode(claims, settings.jwt_secret, algorithm="HS256")


def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    session: Session = Depends(get_session),
) -> User:
    if credentials is None:
        raise ApiError(401, "Unauthorized")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=["HS256"])
    except JWTError:
        raise ApiError(401, "Unauthorized")
    # A valid signature is not enough: the token's email must still resolve to a stored user.
    # This dependency authenticates identity; it does not enforce role or organization access.
    email = payload.get("sub") or ""
    user = session.exec(select(User).where(func.lower(User.email) == email.lower())).first()
    if user is None:
        raise ApiError(401, "Unauthorized")
    return user
