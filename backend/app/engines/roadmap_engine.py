import math


def get_pace_multiplier(learning_pace: str) -> float:
    multipliers = {
        "slow": 0.7,
        "normal": 1.0,
        "fast": 1.3
    }
    return multipliers.get(learning_pace, 1.0)


def generate_weekly_plan(
    ordered_skills: list[dict],
    hours_per_day: float,
    learning_pace: str
) -> list[dict]:
    pace_multiplier = get_pace_multiplier(learning_pace)
    weekly_capacity = hours_per_day * 7 * pace_multiplier

    weeks = []
    current_week_hours = 0
    week_number = 1
    current_week_skills = []

    for skill in ordered_skills:
        remaining_hours = skill["estimated_hours"]

        while remaining_hours > 0:
            space_in_week = weekly_capacity - current_week_hours

            if space_in_week <= 0:
                # Week is full, save and start new
                weeks.append({
                    "week": week_number,
                    "skills": current_week_skills,
                    "total_hours": round(current_week_hours, 1)
                })
                week_number += 1
                current_week_skills = []
                current_week_hours = 0
                space_in_week = weekly_capacity

            hours_this_week = min(remaining_hours, space_in_week)

            # Add skill to current week (partial or full)
            current_week_skills.append({
                "skill_id": skill["skill_id"],
                "skill_name": skill["skill_name"],
                "estimated_hours": skill["estimated_hours"],
                "hours_this_week": round(hours_this_week, 1),
                "category": skill["category"]
            })

            current_week_hours += hours_this_week
            remaining_hours -= hours_this_week

    # Save last week
    if current_week_skills:
        weeks.append({
            "week": week_number,
            "skills": current_week_skills,
            "total_hours": round(current_week_hours, 1)
        })

    return weeks
def check_feasibility(
    ordered_skills: list[dict],
    hours_per_day: float,
    learning_pace: str
) -> dict:
    """
    Check if career is achievable within 52 weeks
    """
    pace_multiplier = get_pace_multiplier(learning_pace)
    weekly_capacity = hours_per_day * 7 * pace_multiplier
    annual_capacity = weekly_capacity * 52

    total_hours = sum(skill["estimated_hours"] for skill in ordered_skills)

    if total_hours > annual_capacity:
        shortfall = round(total_hours - annual_capacity, 1)
        hours_needed = round(total_hours / (7 * 52 * pace_multiplier), 1)
        return {
            "feasible": False,
            "total_hours_required": total_hours,
            "annual_capacity_hours": round(annual_capacity, 1),
            "shortfall_hours": shortfall,
            "message": f"At current pace, this career requires {total_hours} hours but you have {round(annual_capacity, 1)} hours in a year.",
            "suggestion": f"Increase to {hours_needed} hours/day to complete in 1 year."
        }

    weeks_needed = math.ceil(total_hours / weekly_capacity)
    return {
        "feasible": True,
        "total_hours_required": total_hours,
        "annual_capacity_hours": round(annual_capacity, 1),
        "weeks_needed": weeks_needed,
        "message": f"Career is achievable in {weeks_needed} weeks at current pace."
    }