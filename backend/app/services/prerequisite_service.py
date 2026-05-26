from sqlalchemy.orm import Session
from app.models.skill import SkillPrerequisite
from app.engines.prerequisite_engine import topological_sort


def get_ordered_skills(skill_ids: list[str], db: Session) -> list[str]:
    """
    Given a list of skill IDs (the user's missing skills),
    fetch their prerequisite edges from DB and return them
    in the correct learning order.
    """

    # Convert to strings in case UUIDs were passed
    skill_id_strs = [str(s) for s in skill_ids]

    # Fetch only the edges relevant to our skill list
    # We only care about prerequisites WITHIN the missing skills
    edges = db.query(SkillPrerequisite).filter(
        SkillPrerequisite.skill_id.in_(skill_id_strs)
    ).all()

    # Convert edges to list of tuples for the engine
    prerequisites = [
        (str(edge.skill_id), str(edge.requires_skill_id))
        for edge in edges
    ]

    # Run topological sort and return ordered list
    return topological_sort(skill_id_strs, prerequisites)