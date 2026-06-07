# tests/test_readiness_engine.py

import math
from datetime import date, timedelta
from app.engines.readiness_engine import (
    decayed_proficiency,
    compute_readiness_score,
    DECAY_RATE,
    NEEDS_REVIEW_THRESHOLD
)

# ─── Decay Tests ───────────────────────────────────────────────────────────────

def test_decay_zero_days():
    """0 days mein koi decay nahi honi chahiye"""
    result = decayed_proficiency(1.0, 0)
    assert result == 1.0


def test_decay_90_days():
    """90 days baad ~83% rehna chahiye"""
    result = decayed_proficiency(1.0, 90)
    expected = math.exp(-DECAY_RATE * 90)
    assert abs(result - expected) < 0.0001


def test_decay_180_days():
    """180 days baad ~70% rehna chahiye"""
    result = decayed_proficiency(1.0, 180)
    expected = math.exp(-DECAY_RATE * 180)
    assert abs(result - expected) < 0.0001


def test_decay_365_days():
    """365 days baad ~48% rehna chahiye"""
    result = decayed_proficiency(1.0, 365)
    expected = math.exp(-DECAY_RATE * 365)
    assert abs(result - expected) < 0.0001


def test_decay_reduces_over_time():
    """Decay monotonically decrease honi chahiye"""
    d0   = decayed_proficiency(1.0, 0)
    d90  = decayed_proficiency(1.0, 90)
    d180 = decayed_proficiency(1.0, 180)
    d365 = decayed_proficiency(1.0, 365)
    assert d0 > d90 > d180 > d365


# ─── Needs Review Tests ────────────────────────────────────────────────────────

def test_needs_review_flag_triggered():
    """Decayed proficiency < 0.40 hone par needs_review True hona chahiye"""
    career_skills = [
        {"skill_id": "1", "importance_weight": 1.0, "category": "language"}
    ]
    # proficiency=0.5, 400 days → decayed = 0.5 * e^(-0.002*400) ≈ 0.224 → below 0.40
    last_practiced = date.today() - timedelta(days=400)
    user_skills = [
        {"skill_id": "1", "proficiency": 0.5, "last_practiced": last_practiced}
    ]
    result = compute_readiness_score(career_skills, user_skills)
    skill = result["skill_details"][0]
    assert skill["needs_review"] == True


def test_needs_review_flag_not_triggered():
    """Fresh skill needs_review False hona chahiye"""
    career_skills = [
        {"skill_id": "1", "importance_weight": 1.0, "category": "language"}
    ]
    user_skills = [
        {"skill_id": "1", "proficiency": 0.9, "last_practiced": date.today()}
    ]
    result = compute_readiness_score(career_skills, user_skills)
    skill = result["skill_details"][0]
    assert skill["needs_review"] == False


# ─── Score Tests ───────────────────────────────────────────────────────────────

def test_perfect_score():
    """Sab skills known + fresh → score 100.0 hona chahiye"""
    career_skills = [
        {"skill_id": "1", "importance_weight": 1.0, "category": "language"},
        {"skill_id": "2", "importance_weight": 1.0, "category": "framework"},
    ]
    user_skills = [
        {"skill_id": "1", "proficiency": 1.0, "last_practiced": date.today()},
        {"skill_id": "2", "proficiency": 1.0, "last_practiced": date.today()},
    ]
    result = compute_readiness_score(career_skills, user_skills)
    assert result["overall_score"] == 100.0


def test_zero_score_no_skills():
    """Koi skill nahi → score 0.0"""
    career_skills = [
        {"skill_id": "1", "importance_weight": 1.0, "category": "language"},
    ]
    result = compute_readiness_score(career_skills, user_skills=[])
    assert result["overall_score"] == 0.0


def test_weighted_score_higher_weight_matters():
    """Higher weight wali skill zyada score contribute karni chahiye"""
    career_skills = [
        {"skill_id": "1", "importance_weight": 3.0, "category": "language"},  # high weight
        {"skill_id": "2", "importance_weight": 1.0, "category": "language"},  # low weight
    ]
    # Only skill 1 known
    user_skills_1 = [
        {"skill_id": "1", "proficiency": 1.0, "last_practiced": date.today()}
    ]
    # Only skill 2 known
    user_skills_2 = [
        {"skill_id": "2", "proficiency": 1.0, "last_practiced": date.today()}
    ]
    score_high = compute_readiness_score(career_skills, user_skills_1)["overall_score"]
    score_low  = compute_readiness_score(career_skills, user_skills_2)["overall_score"]
    assert score_high > score_low


def test_decay_lowers_score():
    """Old skill ka score fresh skill se kam hona chahiye"""
    career_skills = [
        {"skill_id": "1", "importance_weight": 1.0, "category": "language"}
    ]
    fresh_user = [{"skill_id": "1", "proficiency": 1.0, "last_practiced": date.today()}]
    old_user   = [{"skill_id": "1", "proficiency": 1.0, "last_practiced": date.today() - timedelta(days=365)}]

    fresh_score = compute_readiness_score(career_skills, fresh_user)["overall_score"]
    old_score   = compute_readiness_score(career_skills, old_user)["overall_score"]
    assert fresh_score > old_score


def test_category_breakdown_present():
    """Category breakdown mein sahi categories honi chahiye"""
    career_skills = [
        {"skill_id": "1", "importance_weight": 1.0, "category": "language"},
        {"skill_id": "2", "importance_weight": 1.0, "category": "framework"},
    ]
    user_skills = [
        {"skill_id": "1", "proficiency": 1.0, "last_practiced": date.today()},
    ]
    result = compute_readiness_score(career_skills, user_skills)
    assert "language" in result["category_breakdown"]
    assert "framework" in result["category_breakdown"]


def test_needs_review_count():
    """needs_review_count sahi count kare"""
    career_skills = [
        {"skill_id": "1", "importance_weight": 1.0, "category": "language"},
        {"skill_id": "2", "importance_weight": 1.0, "category": "language"},
    ]
    old_date = date.today() - timedelta(days=400)
    user_skills = [
        {"skill_id": "1", "proficiency": 0.5, "last_practiced": old_date},  # needs review
        {"skill_id": "2", "proficiency": 1.0, "last_practiced": date.today()},  # fine
    ]
    result = compute_readiness_score(career_skills, user_skills)
    assert result["needs_review_count"] == 1