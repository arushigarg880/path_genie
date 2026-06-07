# app/engines/readiness_engine.py

import math
from datetime import date

# DECAY_RATE = 0.002
# Rationale: Based on Ebbinghaus Forgetting Curve.
# At this rate:
#   - After 90 days:  proficiency drops to ~83% of original
#   - After 180 days: proficiency drops to ~70% of original
#   - After 365 days: proficiency drops to ~48% of original
# This feels realistic — a skill practiced 1 year ago is roughly half as effective.
# Value is tunable based on future user feedback data.
DECAY_RATE = 0.002

# Skills below this threshold are flagged as needing review
NEEDS_REVIEW_THRESHOLD = 0.40


def decayed_proficiency(base_proficiency: float, days_since_practiced: int) -> float:
    """
    Compute effective proficiency after decay.
    Formula: base_proficiency × e^(-DECAY_RATE × days)
    """
    return base_proficiency * math.exp(-DECAY_RATE * days_since_practiced)


def compute_readiness_score(
    career_skills: list[dict],
    user_skills: list[dict]
) -> dict:
    """
    Compute weighted readiness score with decay.

    career_skills: list of dicts with keys:
        - skill_id, importance_weight, category

    user_skills: list of dicts with keys:
        - skill_id, proficiency, last_practiced (date object or None)

    Returns:
        - overall_score (float, rounded to 1 decimal)
        - category_breakdown (dict)
        - skill_details (list)
    """
    today = date.today()

    # Build a lookup of user's known skills
    user_skill_map = {}
    for us in user_skills:
        days = (today - us["last_practiced"]).days if us.get("last_practiced") else 0
        decayed = decayed_proficiency(us["proficiency"], days)
        user_skill_map[us["skill_id"]] = {
            "proficiency": us["proficiency"],
            "decayed_proficiency": round(decayed, 4),
            "days_since_practiced": days,
            "needs_review": decayed < NEEDS_REVIEW_THRESHOLD
        }

    # Total weight of all career skills
    total_weight = sum(cs["importance_weight"] for cs in career_skills)

    # Weighted sum using decayed proficiency
    weighted_sum = 0.0
    category_weights = {}   # total weight per category
    category_earned = {}    # earned weight per category
    skill_details = []

    for cs in career_skills:
        sid = cs["skill_id"]
        weight = cs["importance_weight"]
        category = cs.get("category", "other")

        # Track category totals
        category_weights[category] = category_weights.get(category, 0.0) + weight
        category_earned.setdefault(category, 0.0)

        if sid in user_skill_map:
            ud = user_skill_map[sid]
            earned = ud["decayed_proficiency"] * weight
            weighted_sum += earned
            category_earned[category] += earned

            skill_details.append({
                "skill_id": sid,
                "category": category,
                "importance_weight": weight,
                "raw_proficiency": ud["proficiency"],
                "decayed_proficiency": ud["decayed_proficiency"],
                "days_since_practiced": ud["days_since_practiced"],
                "needs_review": ud["needs_review"]
            })
        else:
            # User doesn't have this skill
            skill_details.append({
                "skill_id": sid,
                "category": category,
                "importance_weight": weight,
                "raw_proficiency": 0.0,
                "decayed_proficiency": 0.0,
                "days_since_practiced": None,
                "needs_review": False
            })

    # Overall score
    overall_score = round((weighted_sum / total_weight) * 100, 1) if total_weight > 0 else 0.0

    # Category breakdown
    category_breakdown = {}
    for cat, cat_weight in category_weights.items():
        earned = category_earned.get(cat, 0.0)
        category_breakdown[cat] = round((earned / cat_weight) * 100, 1) if cat_weight > 0 else 0.0

    return {
        "overall_score": overall_score,
        "category_breakdown": category_breakdown,
        "skill_details": skill_details,
        "needs_review_count": sum(1 for s in skill_details if s["needs_review"])
    }