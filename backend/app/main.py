from fastapi import FastAPI
from app.db.session import engine
from app.db.base import Base
from app.models import User
from app.routes.auth import router as auth_router
from app.routes.profile import router as profile_router

app = FastAPI(
    title="PathGenie API",
    version="1.0.0"
)

# Temporary table creation (later replace with Alembic migrations)
Base.metadata.create_all(bind=engine)

# Register routes
app.include_router(auth_router)
app.include_router(profile_router)

@app.get("/")
def root():
    return {"message": "PathGenie backend + database connected"}