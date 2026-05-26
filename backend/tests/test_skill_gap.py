# tests/test_skill_gap.py

from app.engines.skill_gap_engine import analyze_skill_gap

# Fake data — no database needed
# We just test the pure logic

MOCK_CAREER_SKILLS = [
    {"skill_id": "1", "skill_name": "Python",     "importance_weight": 0.95, "is_core": True,  "estimated_hours": 80,  "category": "language"},
    {"skill_id": "2", "skill_name": "SQL",         "importance_weight": 0.85, "is_core": True,  "estimated_hours": 40,  "category": "language"},
    {"skill_id": "3", "skill_name": "Git",         "importance_weight": 0.80, "is_core": True,  "estimated_hours": 20,  "category": "tool"},
    {"skill_id": "4", "skill_name": "FastAPI",     "importance_weight": 0.75, "is_core": True,  "estimated_hours": 40,  "category": "framework"},
    {"skill_id": "5", "skill_name": "Docker",      "importance_weight": 0.65, "is_core": False, "estimated_hours": 30,  "category": "tool"},
    {"skill_id": "6", "skill_name": "GraphQL",     "importance_weight": 0.40, "is_core": False, "estimated_hours": 20,  "category": "concept"},
]


def test_all_skills_missing():
    """User knows nothing — all skills should appear in gap"""
    result = analyze_skill_gap(
        user_skill_ids=[],
        career_skills=MOCK_CAREER_SKILLS
    )
    assert result["total_missing"] == 6
    assert result["total_required"] == 6
    assert len(result["critical"]) == 3        # Python(0.95), SQL(0.85), Git(0.80)
    assert len(result["important"]) == 2       # FastAPI(0.75), Docker(0.65)
    assert len(result["supplementary"]) == 1   # GraphQL(0.40)


def test_known_skill_excluded():
    """User knows Python — it should NOT appear in gap"""
    result = analyze_skill_gap(
        user_skill_ids=["1"],   # Python
        career_skills=MOCK_CAREER_SKILLS
    )
    critical_names = [s["skill_name"] for s in result["critical"]]
    assert "Python" not in critical_names
    assert result["total_missing"] == 5


def test_all_skills_known():
    """User knows everything — gap should be empty"""
    result = analyze_skill_gap(
        user_skill_ids=["1", "2", "3", "4", "5", "6"],
        career_skills=MOCK_CAREER_SKILLS
    )
    assert result["total_missing"] == 0
    assert result["critical"] == []
    assert result["important"] == []
    assert result["supplementary"] == []


def test_tier_classification():
    """Each skill must land in the correct tier"""
    result = analyze_skill_gap(
        user_skill_ids=[],
        career_skills=MOCK_CAREER_SKILLS
    )
    critical_names = [s["skill_name"] for s in result["critical"]]
    important_names = [s["skill_name"] for s in result["important"]]
    supplementary_names = [s["skill_name"] for s in result["supplementary"]]

    # Critical: weight >= 0.80
    assert "Python" in critical_names
    assert "SQL" in critical_names
    assert "Git" in critical_names

    # Important: 0.50 <= weight < 0.80
    assert "FastAPI" in important_names
    assert "Docker" in important_names

    # Supplementary: weight < 0.50
    assert "GraphQL" in supplementary_names
    