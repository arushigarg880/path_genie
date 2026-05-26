from collections import deque


def topological_sort(skills: list[str], prerequisites: list[tuple[str, str]]) -> list[str]:
    """
    skills: list of skill IDs (strings) to order
    prerequisites: list of (skill_id, requires_skill_id) tuples
                   meaning: skill_id DEPENDS ON requires_skill_id
    returns: ordered list of skill IDs (learn this first → last)
    raises: ValueError if a cycle is detected
    """

    # Step 1: Set up in_degree counter and graph for every skill
    # in_degree = how many prerequisites does this skill still have?
    in_degree = {s: 0 for s in skills}
    graph = {s: [] for s in skills}

    # Step 2: Fill in the graph using prerequisite edges
    for skill, prereq in prerequisites:
        if prereq in graph:           # only care about skills in our list
            graph[prereq].append(skill)   # prereq unlocks skill
            in_degree[skill] += 1         # skill has one more dependency

    # Step 3: Start with skills that have NO prerequisites (ready to learn now)
    queue = deque([s for s in skills if in_degree[s] == 0])
    ordered = []

    # Step 4: Process queue
    while queue:
        node = queue.popleft()        # take a ready skill
        ordered.append(node)          # add to result

        for neighbor in graph[node]:  # for every skill this unlocks
            in_degree[neighbor] -= 1  # one less dependency remaining
            if in_degree[neighbor] == 0:  # if fully unlocked
                queue.append(neighbor)    # it's ready to learn now

    # Step 5: Cycle detection
    if len(ordered) != len(skills):
        raise ValueError("Cycle detected in prerequisite graph — invalid seed data")

    return ordered