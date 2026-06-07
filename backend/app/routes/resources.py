# app/routes/resources.py

import os
import json
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.dependencies import get_current_user
from app.models.career import UserCareer
from app.models.resource import SkillResource, CareerProject
from app.models.skill import Skill
from app.services.gap_service import get_skill_gap_for_user

router = APIRouter(prefix="/resources", tags=["Resources"])

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_URL = "https://api.tavily.com/search"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Tavily Search Helper (with DB caching) ────────────────────────────────────

def fetch_resources_from_tavily(skill_name: str, skill_id: str, db: Session) -> list[dict]:
    """
    First checks DB for existing resources.
    If not found, fetches from Tavily and saves to DB for future use.
    Tavily is only called ONCE per skill — ever.
    """

    # Step 1: Check DB first
    existing = db.query(SkillResource).filter(
        SkillResource.skill_id == skill_id
    ).first()

    if existing:
        # Already in DB, no Tavily call needed
        saved = db.query(SkillResource).filter(
            SkillResource.skill_id == skill_id
        ).order_by(SkillResource.priority).all()

        return [
            {
                "id": str(r.id),
                "url": r.url,
                "resource_type": r.resource_type,
                "priority": r.priority
            }
            for r in saved
        ]

    # Step 2: Not in DB, fetch from Tavily
    queries = [
        (f"{skill_name} official documentation", "documentation"),
        (f"{skill_name} beginner tutorial", "tutorial"),
        (f"{skill_name} online course", "course"),
    ]

    results = []
    try:
        for query, resource_type in queries:
            response = httpx.post(
                TAVILY_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {TAVILY_API_KEY}"
                },
                json={
                    "query": query,
                    "max_results": 1,
                    "search_depth": "basic"
                },
                timeout=10.0
            )
            data = response.json()
            if data.get("results"):
                top = data["results"][0]
                results.append({
                    "url": top["url"],
                    "resource_type": resource_type,
                    "priority": len(results) + 1
                })
    except Exception as e:
        print(f"Tavily search failed: {e}")
        return []

    if not results:
        return []

    # Step 3: Save to DB so Tavily is never called again for this skill
    try:
        for r in results:
            new_resource = SkillResource(
                skill_id=skill_id,
                url=r["url"],
                resource_type=r["resource_type"],
                priority=r["priority"]
            )
            db.add(new_resource)
        db.commit()

        # Re-fetch from DB to get proper IDs
        saved = db.query(SkillResource).filter(
            SkillResource.skill_id == skill_id
        ).order_by(SkillResource.priority).all()

        return [
            {
                "id": str(r.id),
                "url": r.url,
                "resource_type": r.resource_type,
                "priority": r.priority
            }
            for r in saved
        ]

    except Exception as e:
        print(f"DB save failed: {e}")
        return results


# ─── Groq Enrichment Helper ────────────────────────────────────────────────────

def enrich_resources_with_ai(skill_name: str, skill_id: str, resources: list[dict], db: Session) -> list[dict]:
    """
    Takes real URLs (from DB or Tavily) and asks Grok to generate
    titles and descriptions only. Never asks Grok to generate URLs.
    """

    # If no curated resources in DB, fetch real URLs from Tavily (with caching)
    if not resources:
        resources = fetch_resources_from_tavily(skill_name, skill_id, db)

    # If still nothing, return empty
    if not resources:
        return []

    # Ask Grok for titles + descriptions only (URLs are already real)
    prompt = f"""You are a learning path expert. For the skill "{skill_name}", I have these learning resources with URLs.
For each resource, generate:
1. A clear, specific title
2. A short "why_learn" (1 sentence explaining why this resource is valuable)

Resources:
{json.dumps([{"url": r["url"], "resource_type": r["resource_type"]} for r in resources], indent=2)}

Respond ONLY with a JSON array, no markdown, no explanation:
[
  {{
    "url": "same url as input",
    "resource_type": "same as input",
    "title": "generated title",
    "why_learn": "one sentence why this is valuable"
  }}
]"""

    try:
        response = httpx.post(
            GROQ_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY}"
            },
            json={
                "model": GROQ_MODEL,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30.0
        )
        data = response.json()
        print("GROQ RESPONSE:", data)
        text = data["choices"][0]["message"]["content"].strip()

        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        enriched = json.loads(text)

        # Attach IDs and priority from original resources
        for i, item in enumerate(enriched):
            if i < len(resources):
                item["id"] = resources[i].get("id")
                item["priority"] = resources[i].get("priority", i + 1)

        return enriched

    except Exception as e:
        print(f"AI enrichment failed: {e}")
        # Fallback: return raw resources without AI descriptions
        return resources


# ─── Groq Project Generation Helper ───────────────────────────────────────────

def generate_projects_with_ai(career_name: str, missing_skills: list[str]) -> list[dict]:
    """
    Asks Grok to generate portfolio project ideas.
    No URLs involved here so hallucination is not a concern.
    """
    prompt = f"""You are a career mentor. A student wants to become a "{career_name}".
Their missing skills are: {", ".join(missing_skills)}.

Generate 4 portfolio projects tailored to help them practice these missing skills.
Each project should be realistic and buildable.

Respond ONLY with a JSON array, no markdown, no explanation:
[
  {{
    "title": "project title",
    "description": "2-3 sentence project description",
    "difficulty": "beginner or intermediate or advanced",
    "skills_practiced": ["skill1", "skill2"]
  }}
]"""

    try:
        response = httpx.post(
            GROQ_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY}"
            },
            json={
                "model": GROQ_MODEL,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=30.0
        )
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()

        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        return json.loads(text)

    except Exception as e:
        print(f"AI project generation failed: {e}")
        return []


# ─── Routes ────────────────────────────────────────────────────────────────────

@router.get("/skill/{skill_id}")
def get_skill_resources(
    skill_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    # Get curated resources from DB
    curated = db.query(SkillResource).filter(
        SkillResource.skill_id == skill_id
    ).order_by(SkillResource.priority).all()

    curated_list = [
        {
            "id": str(r.id),
            "url": r.url,
            "resource_type": r.resource_type,
            "priority": r.priority
        }
        for r in curated
    ]

    # Enrich with AI (Tavily fills in if DB is empty)
    enriched = enrich_resources_with_ai(skill.name, skill_id, curated_list, db)

    return {
        "success": True,
        "message": "Resources retrieved",
        "data": {
            "skill_id": skill_id,
            "skill_name": skill.name,
            "ai_enhanced": True,
            "resources": enriched
        }
    }


@router.get("/gap")
def get_gap_resources(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    gap = get_skill_gap_for_user(current_user.id, db)
    all_missing = gap["critical"] + gap["important"] + gap["supplementary"]

    if not all_missing:
        return {"success": True, "message": "No missing skills", "data": []}

    result = []
    for skill_info in all_missing:
        sid = skill_info["skill_id"]

        # Get curated resources from DB
        curated = db.query(SkillResource).filter(
            SkillResource.skill_id == sid
        ).order_by(SkillResource.priority).all()

        curated_list = [
            {
                "id": str(r.id),
                "url": r.url,
                "resource_type": r.resource_type,
                "priority": r.priority
            }
            for r in curated
        ]

        # Enrich with AI (Tavily fills in if DB is empty)
        enriched = enrich_resources_with_ai(skill_info["skill_name"], sid, curated_list, db)

        result.append({
            "skill_id": sid,
            "skill_name": skill_info["skill_name"],
            "importance": skill_info.get("importance_weight", 0),
            "ai_enhanced": True,
            "resources": enriched
        })

    return {
        "success": True,
        "message": "Gap resources retrieved",
        "data": result
    }


@router.get("/projects")
def get_career_projects(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    active_career = db.query(UserCareer).filter_by(
        user_id=current_user.id,
        is_active=True
    ).first()

    if not active_career:
        raise HTTPException(status_code=400, detail="No active career selected")

    from app.models.career import Career
    career = db.query(Career).filter(Career.id == active_career.career_id).first()
    career_name = career.name if career else "Software Developer"

    gap = get_skill_gap_for_user(current_user.id, db)
    all_missing = gap["critical"] + gap["important"] + gap["supplementary"]
    missing_skill_names = [s["skill_name"] for s in all_missing]

    # Generate AI projects (no URLs, so no hallucination risk)
    ai_projects = generate_projects_with_ai(career_name, missing_skill_names)

    if not ai_projects:
        # Fallback to curated DB projects
        db_projects = db.query(CareerProject).filter(
            CareerProject.career_id == active_career.career_id
        ).all()

        all_skill_ids = []
        for p in db_projects:
            all_skill_ids.extend([str(sid) for sid in p.skills_practiced])

        skill_lookup = {
            str(s.id): s.name
            for s in db.query(Skill).filter(Skill.id.in_(all_skill_ids)).all()
        }

        return {
            "success": True,
            "message": "Career projects retrieved (curated fallback)",
            "data": [
                {
                    "id": str(p.id),
                    "title": p.title,
                    "description": p.description,
                    "difficulty": p.difficulty,
                    "skills_practiced": [
                        {
                            "skill_id": str(sid),
                            "skill_name": skill_lookup.get(str(sid), "Unknown")
                        }
                        for sid in p.skills_practiced
                    ]
                }
                for p in db_projects
            ]
        }

    return {
        "success": True,
        "message": "Career projects retrieved (AI-personalized)",
        "ai_enhanced": True,
        "data": ai_projects
    }