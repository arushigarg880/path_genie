# tests/test_psd_engine.py

import math
from app.engines.psd_engine import compute_psd_score, compute_overall_psd


# ─── compute_psd_score Tests ───────────────────────────────────────────────────

def test_no_prerequisites():
    """Skill with no prereqs — psd_score = raw_score"""
    proficiency_map = {"python": 0.8}
    prereq_map = {}
    result = compute_psd_score("python", proficiency_map, prereq_map)
    assert result == 0.8


def test_satisfied_prerequisites():
    """Skill with fully satisfied prereqs — psd_score close to raw_score"""
    proficiency_map = {
        "docker": 0.8,
        "linux": 1.0   # prereq fully satisfied
    }
    prereq_map = {"docker": ["linux"]}
    result = compute_psd_score("docker", proficiency_map, prereq_map)
    # psd = 0.8 * sqrt(1.0) = 0.8
    assert abs(result - 0.8) < 0.0001


def test_unsatisfied_prerequisites():
    """Skill with weak prereqs — psd_score lower than raw_score"""
    proficiency_map = {
        "docker": 0.8,
        "linux": 0.2   # prereq poorly satisfied
    }
    prereq_map = {"docker": ["linux"]}
    result = compute_psd_score("docker", proficiency_map, prereq_map)
    # psd = 0.8 * sqrt(0.2) ≈ 0.358
    expected = 0.8 * math.sqrt(0.2)
    assert abs(result - expected) < 0.0001


def test_missing_prereq_in_proficiency_map():
    """Prereq not in user map — treated as 0.0"""
    proficiency_map = {"docker": 0.8}
    prereq_map = {"docker": ["linux"]}  # linux not in proficiency_map
    result = compute_psd_score("docker", proficiency_map, prereq_map)
    # psd = 0.8 * sqrt(0.0) = 0.0
    assert result == 0.0


def test_multiple_prerequisites():
    """Multiple prereqs — avg satisfaction used"""
    proficiency_map = {
        "fastapi": 0.9,
        "python": 1.0,
        "rest_apis": 0.6
    }
    prereq_map = {"fastapi": ["python", "rest_apis"]}
    result = compute_psd_score("fastapi", proficiency_map, prereq_map)
    avg = (1.0 + 0.6) / 2  # 0.8
    expected = 0.9 * math.sqrt(0.8)
    assert abs(result - expected) < 0.0001


def test_skill_not_in_proficiency_map():
    """User doesn't know the skill — psd_score = 0.0"""
    proficiency_map = {"linux": 0.9}
    prereq_map = {"docker": ["linux"]}
    result = compute_psd_score("docker", proficiency_map, prereq_map)
    assert result == 0.0


# ─── compute_overall_psd Tests ─────────────────────────────────────────────────

def test_overall_psd_no_prereqs():
    """All skills have no prereqs — psd score = standard weighted score"""
    career_skills = [
        {"skill_id": "python", "importance_weight": 1.0, "category": "language"},
        {"skill_id": "sql",    "importance_weight": 1.0, "category": "language"},
    ]
    proficiency_map = {"python": 1.0, "sql": 1.0}
    prereq_map = {}
    result = compute_overall_psd(career_skills, proficiency_map, prereq_map)
    assert result["overall_psd_score"] == 100.0


def test_prereq_gap_detected():
    """skill with raw - psd > 0.25 should be flagged"""
    career_skills = [
        {"skill_id": "docker", "importance_weight": 1.0, "category": "tool"},
    ]
    proficiency_map = {
        "docker": 0.9,
        "linux": 0.0   # prereq completely missing
    }
    prereq_map = {"docker": ["linux"]}
    result = compute_overall_psd(career_skills, proficiency_map, prereq_map)
    docker_detail = result["skill_details"][0]
    # raw=0.9, psd=0.0, difference=0.9 > 0.25 → gap detected
    assert docker_detail["prereq_gap_detected"] == True
    assert result["prerequisite_gap_count"] == 1


def test_prereq_gap_not_detected():
    """Small difference — no gap flagged"""
    career_skills = [
        {"skill_id": "docker", "importance_weight": 1.0, "category": "tool"},
    ]
    proficiency_map = {
        "docker": 0.8,
        "linux": 1.0   # prereq fully satisfied
    }
    prereq_map = {"docker": ["linux"]}
    result = compute_overall_psd(career_skills, proficiency_map, prereq_map)
    docker_detail = result["skill_details"][0]
    # raw=0.8, psd=0.8, difference=0.0 → no gap
    assert docker_detail["prereq_gap_detected"] == False


def test_explanation_present():
    """FR-8.5: explanation text present in response"""
    career_skills = [
        {"skill_id": "python", "importance_weight": 1.0, "category": "language"},
    ]
    result = compute_overall_psd(career_skills, {"python": 0.5}, {})
    assert "explanation" in result
    assert len(result["explanation"]) > 0