from fastapi import FastAPI
from app.db.session import engine
from app.db.base import Base
from app.models import User
from app.models.skill import Skill, UserSkill,SkillPrerequisite 
from app.routes.auth import router as auth_router
from app.routes.profile import router as profile_router
from app.models.career import Career, CareerSkill, UserCareer,UserRoadmap,RoadmapPhase
from app.seed.seed_data import seed_database
from app.db.session import SessionLocal
from app.routes.careers import router as careers_router
from contextlib import asynccontextmanager
from app.routes.gap import router as gap_router
from app.routes.roadmap import router as roadmap_router
from app.routes.readiness import router as readiness_router
from app.routes.psd import router as psd_router
from app.routes.resources import router as resources_router
Base.metadata.create_all(bind=engine)
from dotenv import load_dotenv
load_dotenv()
@asynccontextmanager
async def lifespan(app):
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="PathGenie API",
    version="1.0.0",
    lifespan=lifespan 
)

# Temporary table creation (later replace with Alembic migrations)


# Register routes
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(careers_router)
app.include_router(gap_router)
app.include_router(roadmap_router)
app.include_router(readiness_router)
app.include_router(psd_router)
app.include_router(resources_router)

@app.get("/")
def root():
    return {"message": "PathGenie backend + database connected"}
