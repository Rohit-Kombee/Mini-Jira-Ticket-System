"""Authentication service."""
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.config import get_settings
from app.models.user import User
from app.schemas.user_schema import UserCreateByAdmin, UserUpdateByAdmin, UserLogin
from app.observability.logging import get_logger
from app.observability.metrics import LOGINS_TOTAL

logger = get_logger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

# Bcrypt accepts at most 72 bytes; truncate to avoid ValueError
BCRYPT_MAX_BYTES = 72


def _truncate_for_bcrypt(password: str) -> str:
    encoded = password.encode("utf-8")
    if len(encoded) <= BCRYPT_MAX_BYTES:
        return password
    return encoded[:BCRYPT_MAX_BYTES].decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    return pwd_context.hash(_truncate_for_bcrypt(password))


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(_truncate_for_bcrypt(plain), hashed)


def create_access_token(user_id: int, email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode = {"sub": str(user_id), "email": email, "exp": expire}
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_users_by_ids(db: Session, ids: list[int]) -> list[User]:
    if not ids:
        return []
    return db.query(User).filter(User.id.in_(ids)).all()


def create_user_by_admin(db: Session, data: UserCreateByAdmin) -> User:
    """Admin creates a user with role developer or qa."""
    if get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("user_created_by_admin", extra={"user_id": user.id, "email": user.email, "role": user.role})
    return user


def update_user_by_admin(db: Session, user_id: int, data: UserUpdateByAdmin) -> User:
    """Admin updates a user. Cannot change another admin's role or delete admin."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.role == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify admin user")
    if data.name is not None:
        user.name = data.name
    if data.email is not None:
        other = get_user_by_email(db, data.email)
        if other and other.id != user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")
        user.email = data.email
    if data.password is not None:
        user.password_hash = hash_password(data.password)
    if data.role is not None:
        if data.role not in ("developer", "qa"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role must be developer or qa")
        user.role = data.role
    db.commit()
    db.refresh(user)
    return user


def delete_user_by_admin(db: Session, user_id: int) -> None:
    """Admin deletes a user. Cannot delete an admin."""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.role == "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete admin user")
    db.delete(user)
    db.commit()
    logger.info("user_deleted_by_admin", extra={"user_id": user_id})


def authenticate_user(db: Session, data: UserLogin) -> User | None:
    # Default admin can log in with email "admin" or "admin@localhost"
    email = data.email.strip().lower()
    if email == "admin":
        email = "admin@localhost"
    user = get_user_by_email(db, email)
    if not user or not verify_password(data.password, user.password_hash):
        logger.warning("login_failed", extra={"email": data.email})
        return None
    return user


def list_users(db: Session, role_filter: str | None = None) -> list[User]:
    q = db.query(User)
    if role_filter:
        roles = [r.strip().lower() for r in role_filter.split(",") if r.strip()]
        # Backward compat: developer <-> agent, qa <-> viewer
        expanded = set(roles)
        if "developer" in expanded:
            expanded.add("agent")
        if "agent" in expanded:
            expanded.add("developer")
        if "qa" in expanded:
            expanded.add("viewer")
        if "viewer" in expanded:
            expanded.add("qa")
        if expanded:
            q = q.filter(User.role.in_(expanded))
    return q.order_by(User.name).all()


def get_current_user_from_token(db: Session, token: str) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
        user_id = int(sub)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
