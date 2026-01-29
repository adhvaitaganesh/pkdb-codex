from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.config import settings
from app.models import UserRecord
from app.storage import InMemoryStore, MongoStore, Storage

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
_store: Storage | None = None


def get_store() -> Storage:
    global _store
    if _store is None:
        if settings.use_mongo:
            _store = MongoStore(settings.mongo_uri, settings.mongo_db)
        else:
            _store = InMemoryStore()
    return _store


def get_current_user(
    token: str = Depends(oauth2_scheme),
    store: Storage = Depends(get_store),
) -> UserRecord:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise credentials_exception from exc
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception
    user = store.get_user(user_id)
    if not user:
        raise credentials_exception
    return user
