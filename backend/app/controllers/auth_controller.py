"""Auth API controller."""
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user_schema import UserResponse, UserLogin, Token
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    get_current_user_from_token,
)
from app.observability.tracing import get_tracer
from app.observability.logging import get_logger
from app.observability.metrics import LOGINS_TOTAL, active_users_inc, active_users_dec

router = APIRouter(prefix="/auth", tags=["auth"])
tracer = get_tracer(__name__)
logger = get_logger(__name__)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = auth.split(" ")[1]
    return get_current_user_from_token(db, token)


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    with tracer.start_as_current_span("auth_login_controller"):
        user = authenticate_user(db, data)
        if not user:
            logger.warning("login_failed_validation", extra={"email": data.email})
            from fastapi import HTTPException
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        token = create_access_token(user.id, user.email)
        LOGINS_TOTAL.inc()
        active_users_inc()
        return Token(access_token=token)


@router.post("/logout")
def logout(user: User = Depends(get_current_user)):
    """Decrement active users gauge (for observability). No server-side session to clear."""
    active_users_dec()
    return {"status": "ok"}


@router.get("/me", response_model=UserResponse)
def me(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )
