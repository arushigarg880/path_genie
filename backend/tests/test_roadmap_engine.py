import math
from app.engines.roadmap_engine import generate_weekly_plan, get_pace_multiplier, check_feasibility


# Mock skills data
MOCK_SKILLS = [
    {"skill_id": "1", "skill_name": "Python",    "estimated_hours": 80, "category": "language"},
    {"skill_id": "2", "skill_name": "SQL",        "estimated_hours": 40, "category": "language"},
    {"skill_id": "3", "skill_name": "Git",        "estimated_hours": 20, "category": "tool"},
    {"skill_id": "4", "skill_name": "REST APIs",  "estimated_hours": 25, "category": "concept"},
]


# Test 1: Pace multiplier values correct hain
def test_pace_multipliers():
    assert get_pace_multiplier("slow")   == 0.7
    assert get_pace_multiplier("normal") == 1.0
    assert get_pace_multiplier("fast")   == 1.3


# Test 2: FIXED — exact week count, not loose >= 10
def test_correct_phase_count():
    result = generate_weekly_plan(MOCK_SKILLS, hours_per_day=2, learning_pace="normal")
    total_hours = sum(s["estimated_hours"] for s in MOCK_SKILLS)  # 165
    weekly_capacity = 2 * 7 * 1.0                                 # 14
    expected_weeks = math.ceil(total_hours / weekly_capacity)      # 12
    assert len(result) == expected_weeks


# Test 3: Fast pace mein kam weeks lagte hain slow se
def test_fast_pace_fewer_weeks():
    slow_result = generate_weekly_plan(MOCK_SKILLS, hours_per_day=3, learning_pace="slow")
    fast_result = generate_weekly_plan(MOCK_SKILLS, hours_per_day=3, learning_pace="fast")
    assert len(fast_result) <= len(slow_result)


# Test 4: Har week mein weekly capacity exceed nahi honi chahiye
def test_weekly_capacity_not_exceeded():
    hours_per_day = 2
    pace = "normal"
    weekly_capacity = hours_per_day * 7 * 1.0  # 14 hrs

    result = generate_weekly_plan(MOCK_SKILLS, hours_per_day=hours_per_day, learning_pace=pace)

    for week in result:
        assert week["total_hours"] <= weekly_capacity


# Test 5: FIXED — set() nahi, actual hours verify karo per skill
def test_no_skills_missing():
    result = generate_weekly_plan(MOCK_SKILLS, hours_per_day=3, learning_pace="normal")

    hours_per_skill = {}
    for week in result:
        for skill in week["skills"]:
            sid = skill["skill_id"]
            hours_per_skill[sid] = hours_per_skill.get(sid, 0) + skill["hours_this_week"]

    for skill in MOCK_SKILLS:
        assert skill["skill_id"] in hours_per_skill
        assert abs(hours_per_skill[skill["skill_id"]] - skill["estimated_hours"]) < 0.01


# Test 6: ADDED — feasibility fail case
def test_feasibility_not_achievable():
    heavy_skills = [{"skill_id": "x", "skill_name": "X", "estimated_hours": 5000, "category": "concept"}]
    result = check_feasibility(heavy_skills, hours_per_day=1, learning_pace="slow")
    assert result["feasible"] == False
    assert "shortfall_hours" in result
    assert result["shortfall_hours"] > 0


# Test 7: ADDED — feasibility pass case
def test_feasibility_achievable():
    light_skills = [{"skill_id": "x", "skill_name": "X", "estimated_hours": 10, "category": "concept"}]
    result = check_feasibility(light_skills, hours_per_day=2, learning_pace="normal")
    assert result["feasible"] == True
    assert result["weeks_needed"] == 1