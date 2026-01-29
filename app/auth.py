from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.config import settings
from app.models import Role, UserRecord

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(user: UserRecord) -> str:
    expires = datetime.utcnow() + timedelta(minutes=settings.access_token_minutes)
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "exp": expires,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def require_role(user: UserRecord, allowed: set[Role]) -> None:
    if user.role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
