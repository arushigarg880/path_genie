from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import decode_token
from app.db.session import get_db

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user_id = payload.get("user_id")

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user
def require_complete_profile(
    current_user: User = Depends(get_current_user)
):
    required_fields = [
        current_user.education,
        current_user.academic_year,
        current_user.hours_per_day,
        current_user.learning_pace
    ]
    if not all(required_fields):
        raise HTTPException(
            status_code=400,
            detail="Please complete your profile before accessing this feature"
        )
    return current_user