from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.dependencies import get_current_user
from app.models.career import UserCareer, UserRoadmap, RoadmapPhase
from app.models.skill import Skill
from app.services.gap_service import get_skill_gap_for_user
from app.services.prerequisite_service import get_ordered_skills
from app.engines.roadmap_engine import generate_weekly_plan, check_feasibility

router = APIRouter(prefix="/roadmap", tags=["Roadmap"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/generate")
def generate_roadmap(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Step 1: Get user's active career
    active_career = db.query(UserCareer).filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()

    if not active_career:
        raise HTTPException(status_code=400, detail="No active career selected")

    # Step 1.5: Profile completeness check (FR-6.1)
    if not current_user.hours_per_day or not current_user.learning_pace:
        raise HTTPException(
            status_code=400,
            detail="Complete your profile first (hours_per_day and learning_pace required)"
        )

    # Step 2: Get missing skills from M4
    gap = get_skill_gap_for_user(current_user.id, db)
    all_missing = gap["critical"] + gap["important"] + gap["supplementary"]

    if not all_missing:
        return {"success": True, "message": "No missing skills — you are ready!", "data": []}

    # Step 3: Get just the skill IDs
    missing_skill_ids = [cs["skill_id"] for cs in all_missing]

    # Step 4: Run topological sort to get correct learning order
    try:
        ordered_ids = get_ordered_skills(missing_skill_ids, db)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Step 5: Track old roadmap versions
    old_roadmaps = db.query(UserRoadmap).filter_by(
        user_id=current_user.id,
        career_id=active_career.career_id
    ).all()
    last_version = 0
    for r in old_roadmaps:
        last_version = max(last_version, r.version)

    # Step 6: Build roadmap_data (list of skill info in order)
    skill_lookup = {str(s.id): s for s in db.query(Skill).all()}
    roadmap_data = []
    for i, skill_id in enumerate(ordered_ids):
        skill = skill_lookup.get(skill_id)
        if skill:
            roadmap_data.append({
                "phase": i + 1,
                "skill_id": skill_id,
                "skill_name": skill.name,
                "estimated_hours": skill.estimated_hours,
                "category": skill.category
            })

    # Step 6b: Feasibility check PEHLE (FR-6.6)
    hours_per_day = current_user.hours_per_day
    learning_pace = current_user.learning_pace.value

    feasibility = check_feasibility(
        ordered_skills=roadmap_data,
        hours_per_day=hours_per_day,
        learning_pace=learning_pace
    )

    # Step 6c: Weekly plan BAAD MEIN
    weekly_plan = generate_weekly_plan(
        ordered_skills=roadmap_data,
        hours_per_day=hours_per_day,
        learning_pace=learning_pace
    )

    # Step 7: Save new roadmap to DB
    new_roadmap = UserRoadmap(
        user_id=current_user.id,
        career_id=active_career.career_id,
        roadmap_data=roadmap_data,
        version=last_version + 1,
        stability_score=1.0
    )
    db.add(new_roadmap)
    db.flush()

    # Step 8: Save individual phases
    for i, skill_id in enumerate(ordered_ids):
        phase = RoadmapPhase(
            roadmap_id=new_roadmap.id,
            phase_number=i + 1,
            skill_id=skill_id,
            status="pending"
        )
        db.add(phase)

    db.commit()

    weekly_capacity = round(
        hours_per_day * 7 *
        {"slow": 0.7, "normal": 1.0, "fast": 1.3}.get(learning_pace, 1.0), 1
    )

    return {
        "success": True,
        "message": "Roadmap generated successfully" if feasibility["feasible"] else "Roadmap generated but career not achievable in 1 year at current pace",
        "data": {
            "roadmap_id": str(new_roadmap.id),
            "version": new_roadmap.version,
            "total_phases": len(ordered_ids),
            "total_weeks": len(weekly_plan),
            "weekly_capacity_hours": weekly_capacity,
            "feasibility": feasibility,
            "phases": roadmap_data,
            "weekly_plan": weekly_plan
        }
    }


@router.get("")
def get_roadmap(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    roadmap = db.query(UserRoadmap).filter_by(
        user_id=current_user.id
    ).order_by(UserRoadmap.version.desc()).first()

    if not roadmap:
        raise HTTPException(status_code=404, detail="No roadmap found. Generate one first.")

    return {
        "success": True,
        "message": "Roadmap retrieved",
        "data": {
            "roadmap_id": str(roadmap.id),
            "version": roadmap.version,
            "generated_at": str(roadmap.generated_at),
            "total_phases": len(roadmap.roadmap_data),
            "phases": roadmap.roadmap_data
        }
    }


@router.get("/history")
def get_roadmap_history(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    roadmaps = db.query(UserRoadmap).filter_by(
        user_id=current_user.id
    ).order_by(UserRoadmap.version.desc()).all()

    if not roadmaps:
        raise HTTPException(status_code=404, detail="No roadmaps found")

    return {
        "success": True,
        "message": "Roadmap history retrieved",
        "data": [
            {
                "roadmap_id": str(r.id),
                "version": r.version,
                "generated_at": str(r.generated_at),
                "total_phases": len(r.roadmap_data),
                "stability_score": r.stability_score
            }
            for r in roadmaps
        ]
    }


@router.patch("/phases/{phase_id}")
def mark_phase_complete(
    phase_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from datetime import datetime, timezone

    phase = db.query(RoadmapPhase).filter(
        RoadmapPhase.id == phase_id
    ).first()

    if not phase:
        raise HTTPException(status_code=404, detail="Phase not found")

    roadmap = db.query(UserRoadmap).filter(
        UserRoadmap.id == phase.roadmap_id,
        UserRoadmap.user_id == current_user.id
    ).first()

    if not roadmap:
        raise HTTPException(status_code=403, detail="Not your roadmap")

    phase.status = "completed"
    phase.completed_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "success": True,
        "message": f"Phase {phase.phase_number} marked as completed",
        "data": {
            "phase_id": str(phase.id),
            "phase_number": phase.phase_number,
            "status": phase.status,
            "completed_at": str(phase.completed_at)
        }
    }