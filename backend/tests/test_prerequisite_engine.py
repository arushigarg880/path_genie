import pytest
from app.engines.prerequisite_engine import topological_sort


# Test 1: Skills with no prerequisites at all
# All skills are independent, no edges
# Result: all skills present, any order is valid
def test_no_prerequisites():
    skills = ["Python", "SQL", "Git"]
    prerequisites = []
    result = topological_sort(skills, prerequisites)
    assert set(result) == set(skills)  # all skills present
    assert len(result) == 3            # no duplicates


# Test 2: Simple chain — A → B → C
# Must learn Python before Pandas, Pandas before Scikit-learn
def test_simple_chain():
    skills = ["Scikit-learn", "Pandas", "Python"]
    prerequisites = [
        ("Pandas",       "Python"),       # Pandas requires Python
        ("Scikit-learn", "Pandas"),       # Scikit-learn requires Pandas
    ]
    result = topological_sort(skills, prerequisites)
    assert result.index("Python") < result.index("Pandas")
    assert result.index("Pandas") < result.index("Scikit-learn")


# Test 3: Multiple prerequisites for one skill
# Scikit-learn requires Python, Statistics, AND NumPy
def test_multiple_prerequisites():
    skills = ["Python", "Statistics", "NumPy", "Scikit-learn"]
    prerequisites = [
        ("Scikit-learn", "Python"),
        ("Scikit-learn", "Statistics"),
        ("Scikit-learn", "NumPy"),
    ]
    result = topological_sort(skills, prerequisites)
    assert result.index("Python")     < result.index("Scikit-learn")
    assert result.index("Statistics") < result.index("Scikit-learn")
    assert result.index("NumPy")      < result.index("Scikit-learn")


# Test 4: Cycle detection — A requires B, B requires A (impossible)
# Must raise ValueError
def test_cycle_detection():
    skills = ["A", "B"]
    prerequisites = [
        ("A", "B"),  # A requires B
        ("B", "A"),  # B requires A  ← cycle!
    ]
    with pytest.raises(ValueError, match="Cycle detected"):
        topological_sort(skills, prerequisites)


# Test 5: Disconnected graph — two separate chains, no connection
def test_disconnected_graph():
    skills = ["Python", "FastAPI", "JavaScript", "React"]
    prerequisites = [
        ("FastAPI", "Python"),      # Python chain
        ("React",   "JavaScript"),  # JavaScript chain
    ]
    result = topological_sort(skills, prerequisites)
    assert result.index("Python")     < result.index("FastAPI")
    assert result.index("JavaScript") < result.index("React")
    assert len(result) == 4