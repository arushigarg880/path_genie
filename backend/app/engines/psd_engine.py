import math


def get_all_prerequisites(
    skill_id: str,
    prerequisite_map: dict,
    visited: set = None
) -> list[str]:
    """
    Recursively fetch entire prerequisite chain from DAG.
    Cycle protection via visited set.
    """
    if visited is None:
        visited = set()

    if skill_id in visited:
        return []

    visited.add(skill_id)
    direct_prereqs = prerequisite_map.get(skill_id, [])
    all_prereqs = list(direct_prereqs)

    for prereq in direct_prereqs:
        deeper = get_all_prerequisites(prereq, prerequisite_map, visited)
        all_prereqs.extend(deeper)

    return list(set(all_prereqs))  # deduplicate


def compute_psd_score(
    skill_id: str,
    user_proficiency_map: dict[str, float],
    prerequisite_map: dict[str, list[str]]
) -> float:
    """
    Compute PSD-adjusted score for a single skill.

    Formula: psd_score = raw_score × sqrt(avg_prerequisite_satisfaction)

    If skill has no prerequisites, psd_score = raw_score.

    Args:
        skill_id: skill being evaluated
        user_proficiency_map: {skill_id: decayed_proficiency}
        prerequisite_map: {skill_id: [list of prerequisite skill_ids]}
    """
    # FR-8.1: recursively fetch full chain
    prereqs = get_all_prerequisites(skill_id, prerequisite_map)

    if not prereqs:
        return user_proficiency_map.get(skill_id, 0.0)

    prereq_scores = [
        user_proficiency_map.get(p, 0.0) for p in prereqs
    ]
    avg_prereq_satisfaction = sum(prereq_scores) / len(prereq_scores)
    raw = user_proficiency_map.get(skill_id, 0.0)

    return raw * math.sqrt(avg_prereq_satisfaction)


def compute_overall_psd(
    career_skills: list[dict],
    user_proficiency_map: dict[str, float],
    prerequisite_map: dict[str, list[str]]
) -> dict:
    """
    Compute PSD readiness score for all career skills.

    Args:
        career_skills: list of dicts with skill_id, importance_weight, category
        user_proficiency_map: {skill_id: decayed_proficiency}
        prerequisite_map: {skill_id: [list of prereq skill_ids]}

    Returns:
        overall_psd_score, skill_details, prerequisite_gap_count
    """
    total_weight = sum(cs["importance_weight"] for cs in career_skills)
    weighted_psd_sum = 0.0
    skill_details = []

    for cs in career_skills:
        sid = cs["skill_id"]
        weight = cs["importance_weight"]

        raw_score = user_proficiency_map.get(sid, 0.0)
        psd = compute_psd_score(sid, user_proficiency_map, prerequisite_map)
        psd = round(psd, 4)

        # FR-8.6: flag if psd significantly lower than raw (difference > 0.25)
        prereq_gap_detected = (raw_score - psd) > 0.25

        weighted_psd_sum += psd * weight

        skill_details.append({
            "skill_id": sid,
            "category": cs.get("category", "other"),
            "importance_weight": weight,
            "raw_score": round(raw_score, 4),
            "psd_score": psd,
            "prereq_gap_detected": prereq_gap_detected,
            "prerequisites": get_all_prerequisites(sid, prerequisite_map)
        })

    overall_psd_score = round(
        (weighted_psd_sum / total_weight) * 100, 1
    ) if total_weight > 0 else 0.0

    return {
        "overall_psd_score": overall_psd_score,
        "skill_details": skill_details,
        "prerequisite_gap_count": sum(1 for s in skill_details if s["prereq_gap_detected"]),
        "explanation": "This score reflects how well your foundational skills support your advanced knowledge."
    }