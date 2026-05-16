from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.auth import UserRegister, UserLogin
from app.models.user import User
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)
from app.core.dependencies import (
    get_db,
    get_current_user
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register")
def register(
    user: UserRegister,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    new_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully"
    }


@router.post("/login")
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not verify_password(
        user.password,
        existing_user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token(
        {"user_id": str(existing_user.id)}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": str(current_user.id),
        "name": current_user.name,
        "email": current_user.email
    }