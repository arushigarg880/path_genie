import uuid
import enum
from sqlalchemy import Enum as SAEnum   
from sqlalchemy import Column, String, DateTime,Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base
from app.core.enums import LearningPace

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name = Column(String(100), nullable=False)

    email = Column(String(255), unique=True, nullable=False)

    hashed_password = Column(String, nullable=False)

    academic_year = Column(String(50), nullable=True)

    education = Column(String(100), nullable=True)

    hours_per_day = Column(Float, nullable=True)

    learning_pace = Column(SAEnum(LearningPace), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )