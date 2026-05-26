from sqlalchemy.orm import Session
from app.models.career import Career, CareerSkill
from app.models.skill import Skill
import uuid

SKILLS = [
    {"name": "Python", "description": "Python programming language", "estimated_hours": 80, "category": "language"},
    {"name": "JavaScript", "description": "JavaScript programming language", "estimated_hours": 80, "category": "language"},
    {"name": "SQL", "description": "Structured Query Language", "estimated_hours": 40, "category": "language"},
    {"name": "HTML", "description": "HyperText Markup Language", "estimated_hours": 20, "category": "language"},
    {"name": "CSS", "description": "Cascading Style Sheets", "estimated_hours": 20, "category": "language"},
    {"name": "Git", "description": "Version control system", "estimated_hours": 20, "category": "tool"},
    {"name": "Docker", "description": "Containerization platform", "estimated_hours": 30, "category": "tool"},
    {"name": "Linux Basics", "description": "Linux command line fundamentals", "estimated_hours": 20, "category": "tool"},
    {"name": "FastAPI", "description": "Python web framework", "estimated_hours": 40, "category": "framework"},
    {"name": "React", "description": "JavaScript UI library", "estimated_hours": 60, "category": "framework"},
    {"name": "PostgreSQL", "description": "Relational database system", "estimated_hours": 35, "category": "tool"},
    {"name": "REST APIs", "description": "RESTful API design principles", "estimated_hours": 25, "category": "concept"},
    {"name": "Statistics", "description": "Statistical concepts for data analysis", "estimated_hours": 60, "category": "concept"},
    {"name": "Linear Algebra", "description": "Linear algebra for ML", "estimated_hours": 50, "category": "concept"},
    {"name": "Machine Learning", "description": "ML fundamentals", "estimated_hours": 100, "category": "concept"},
    {"name": "Pandas", "description": "Python data analysis library", "estimated_hours": 40, "category": "library"},
    {"name": "NumPy", "description": "Numerical computing library", "estimated_hours": 30, "category": "library"},
    {"name": "Scikit-learn", "description": "ML library for Python", "estimated_hours": 50, "category": "library"},
    {"name": "Matplotlib", "description": "Data visualization library", "estimated_hours": 25, "category": "library"},
    {"name": "TensorFlow", "description": "Deep learning framework", "estimated_hours": 80, "category": "library"},
]

CAREERS = [
    {"name": "Backend Developer", "description": "Build server-side applications", "math_intensity": 2, "coding_intensity": 5, "estimated_prep_weeks": 24},
    {"name": "Frontend Developer", "description": "Build user interfaces", "math_intensity": 1, "coding_intensity": 4, "estimated_prep_weeks": 20},
    {"name": "Data Analyst", "description": "Analyze and visualize data", "math_intensity": 3, "coding_intensity": 3, "estimated_prep_weeks": 20},
    {"name": "Data Scientist", "description": "Build predictive models", "math_intensity": 5, "coding_intensity": 4, "estimated_prep_weeks": 36},
    {"name": "Machine Learning Engineer", "description": "Deploy ML models", "math_intensity": 5, "coding_intensity": 5, "estimated_prep_weeks": 48},
    {"name": "Full Stack Developer", "description": "Build end-to-end applications", "math_intensity": 2, "coding_intensity": 5, "estimated_prep_weeks": 36},
]

# career name → list of (skill_name, importance_weight, is_core)
CAREER_SKILLS = {
    "Backend Developer": [
        ("Python",    0.95, True),
        ("SQL",       0.85, True),
        ("Git",       0.80, True),
        ("REST APIs", 0.85, True),
        ("FastAPI",   0.75, True),
        ("Docker",    0.65, False),
        ("Linux Basics", 0.60, False),
        ("PostgreSQL",0.70, True),
    ],
    "Frontend Developer": [
        ("JavaScript",0.95, True),
        ("HTML",      0.90, True),
        ("CSS",       0.90, True),
        ("React",     0.85, True),
        ("Git",       0.75, True),
        ("REST APIs", 0.65, False),
    ],
    "Data Analyst": [
        ("Python",    0.85, True),
        ("SQL",       0.90, True),
        ("Statistics",0.80, True),
        ("Pandas",    0.85, True),
        ("Matplotlib",0.70, True),
        ("Git",       0.55, False),
        ("NumPy",     0.65, False),
    ],
    "Data Scientist": [
        ("Python",       0.95, True),
        ("Statistics",   0.90, True),
        ("Linear Algebra",0.80, True),
        ("Pandas",       0.90, True),
        ("NumPy",        0.85, True),
        ("Scikit-learn", 0.85, True),
        ("Matplotlib",   0.70, False),
        ("SQL",          0.65, False),
        ("Machine Learning", 0.90, True),
        ("Git",          0.60, False),
    ],
    "Machine Learning Engineer": [
        ("Python",       0.95, True),
        ("Machine Learning", 0.95, True),
        ("Scikit-learn", 0.85, True),
        ("TensorFlow",   0.85, True),
        ("NumPy",        0.85, True),
        ("Pandas",       0.80, True),
        ("Statistics",   0.85, True),
        ("Linear Algebra",0.85, True),
        ("Docker",       0.70, True),
        ("SQL",          0.55, False),
        ("Git",          0.65, False),
        ("Linux Basics", 0.65, False),
    ],
    "Full Stack Developer": [
        ("Python",      0.85, True),
        ("JavaScript",  0.85, True),
        ("HTML",        0.80, True),
        ("CSS",         0.80, True),
        ("React",       0.80, True),
        ("FastAPI",     0.75, True),
        ("SQL",         0.75, True),
        ("REST APIs",   0.80, True),
        ("Git",         0.75, True),
        ("Docker",      0.55, False),
        ("PostgreSQL",  0.60, False),
    ],
}

SKILL_PREREQUISITES = [
    # Python is required by many
    ("FastAPI",          "Python"),
    ("Pandas",           "Python"),
    ("NumPy",            "Python"),
    ("Scikit-learn",     "Python"),
    ("TensorFlow",       "Python"),
    ("Matplotlib",       "Python"),
    ("Machine Learning", "Python"),

    # Pandas and NumPy required before ML libs
    ("Scikit-learn",     "Pandas"),
    ("Scikit-learn",     "NumPy"),
    ("Scikit-learn",     "Statistics"),
    ("TensorFlow",       "NumPy"),
    ("TensorFlow",       "Scikit-learn"),
    ("TensorFlow",       "Linear Algebra"),
    ("Machine Learning", "Statistics"),

    # JavaScript ecosystem
    ("React",            "JavaScript"),
    ("React",            "HTML"),
    ("React",            "CSS"),

    # Docker needs Linux
    ("Docker",           "Linux Basics"),

    # PostgreSQL needs SQL basics
    ("PostgreSQL",       "SQL"),

    # FastAPI needs REST APIs understanding
    ("FastAPI",          "REST APIs"),
]


def seed_database(db: Session):
    # Step 1: Seed Skills
    if db.query(Skill).count() == 0:
        for skill_data in SKILLS:
            skill = Skill(**skill_data)
            db.add(skill)
        db.commit()
        print("✅ Skills seeded.")

    # Step 2: Seed Careers
    if db.query(Career).count() == 0:
        for career_data in CAREERS:
            career = Career(**career_data)
            db.add(career)
        db.commit()
        print("✅ Careers seeded.")

    # Step 3: Seed CareerSkills (the junction table)
    # Why here? Because we need skills and careers to exist first so we can look up their UUIDs
    if db.query(CareerSkill).count() == 0:
        # Build lookup dictionaries: name → UUID
        skill_map = {s.name: s.id for s in db.query(Skill).all()}
        career_map = {c.name: c.id for c in db.query(Career).all()}

        for career_name, skill_list in CAREER_SKILLS.items():
            career_id = career_map.get(career_name)
            if not career_id:
                print(f"⚠️  Career not found: {career_name}")
                continue

            for skill_name, weight, is_core in skill_list:
                skill_id = skill_map.get(skill_name)
                if not skill_id:
                    print(f"⚠️  Skill not found: {skill_name}")
                    continue

                cs = CareerSkill(
                    career_id=career_id,
                    skill_id=skill_id,
                    importance_weight=weight,
                    is_core=is_core
                )
                db.add(cs)

        db.commit()
        print("✅ CareerSkills seeded.")
    seed_prerequisites(db)
def seed_prerequisites(db: Session):
    from app.models.skill import SkillPrerequisite

    if db.query(SkillPrerequisite).count() == 0:
        skill_map = {s.name: s.id for s in db.query(Skill).all()}

        for skill_name, requires_name in SKILL_PREREQUISITES:
            skill_id = skill_map.get(skill_name)
            requires_id = skill_map.get(requires_name)

            if not skill_id:
                print(f"⚠️  Skill not found: {skill_name}")
                continue
            if not requires_id:
                print(f"⚠️  Prerequisite skill not found: {requires_name}")
                continue

            prereq = SkillPrerequisite(
                skill_id=skill_id,
                requires_skill_id=requires_id
            )
            db.add(prereq)

        try:
            db.commit()
            print("✅ Prerequisites seeded.")
        except Exception as e:
            db.rollback()
            print(f"❌ Error seeding prerequisites: {e}")
    else:
        print("ℹ️  Prerequisites already seeded, skipping.")