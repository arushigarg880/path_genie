# engines/skill_gap_engine.py

# WHY THIS FILE EXISTS:
# This is pure logic — no database, no FastAPI, no HTTP.
# We separate it so it can be tested independently and reused anywhere.

def analyze_skill_gap(user_skill_ids: list, career_skills: list) -> dict:
    """
    user_skill_ids : list of skill UUIDs the user already knows
    career_skills  : list of dicts, each with keys:
                       - skill_id
                       - skill_name
                       - importance_weight
                       - is_core
    
    Returns a dict with three tiers of missing skills.
    """

    # Convert to a set for O(1) lookup
    # WHY SET? If user has 50 skills and career needs 20,
    # checking "is skill_id in user_skill_ids" 20 times is slow with a list.
    # A set makes each check instant.
    known = set(str(sid) for sid in user_skill_ids)

    # Find missing skills — career needs it but user doesn't have it
    missing = [
        cs for cs in career_skills
        if str(cs["skill_id"]) not in known
    ]

    # Split into tiers based on importance_weight
    critical = [
        s for s in missing if s["importance_weight"] >= 0.80
    ]
    important = [
        s for s in missing if 0.50 <= s["importance_weight"] < 0.80
    ]
    supplementary = [
        s for s in missing if s["importance_weight"] < 0.50
    ]

    return {
        "critical": critical,
        "important": important,
        "supplementary": supplementary,
        "total_missing": len(missing),
        "total_required": len(career_skills)
    }