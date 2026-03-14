"""Users API (admin only)."""
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user_schema import UserResponse, UserCreateByAdmin, UserUpdateByAdmin
from app.services.auth_service import (
    get_current_user_from_token,
    list_users,
    create_user_by_admin,
    update_user_by_admin,
    delete_user_by_admin,
)

router = APIRouter(prefix="/users", tags=["users"])


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = auth.split(" ")[1]
    return get_current_user_from_token(db, token)


def require_admin(user: User = Depends(get_current_user)) -> User:
    from fastapi import HTTPException
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return user


@router.get("", response_model=list[UserResponse])
def list_users_api(
    role: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    """List users. Admin only. Use ?role=developer,qa to filter."""
    users = list_users(db, role_filter=role)
    return [
        UserResponse(
            id=u.id,
            name=u.name,
            email=u.email,
            role=u.role,
            created_at=u.created_at.isoformat() if u.created_at else None,
        )
        for u in users
    ]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_api(
    data: UserCreateByAdmin,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    """Create a user (developer or qa). Admin only."""
    new_user = create_user_by_admin(db, data)
    return UserResponse(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email,
        role=new_user.role,
        created_at=new_user.created_at.isoformat() if new_user.created_at else None,
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user_api(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    """Get one user by id. Admin only."""
    from app.services.auth_service import get_user_by_id
    u = get_user_by_id(db, user_id)
    if not u:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse(
        id=u.id,
        name=u.name,
        email=u.email,
        role=u.role,
        created_at=u.created_at.isoformat() if u.created_at else None,
    )


@router.patch("/{user_id}", response_model=UserResponse)
def update_user_api(
    user_id: int,
    data: UserUpdateByAdmin,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    """Update a user. Admin only. Cannot modify admin users."""
    u = update_user_by_admin(db, user_id, data)
    return UserResponse(
        id=u.id,
        name=u.name,
        email=u.email,
        role=u.role,
        created_at=u.created_at.isoformat() if u.created_at else None,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_api(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    """Delete a user. Admin only. Cannot delete admin."""
    delete_user_by_admin(db, user_id)
