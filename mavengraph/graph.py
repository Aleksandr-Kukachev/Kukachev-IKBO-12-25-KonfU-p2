"""Iterative DFS with re-expansion when a shorter path is discovered."""


def build_graph(repository, root, max_depth, substring=""):
    graph = {root: []}
    best_depth = {}
    stack = [(root, 0)]
    while stack:
        node, depth = stack.pop()
        if depth >= best_depth.get(node, float("inf")):
            continue
        best_depth[node] = depth
        graph.setdefault(node, [])
        if depth >= max_depth:
            continue
        children = []
        for child in repository.dependencies(node):
            name = child.split(":")[1] if ":" in child else child
            if substring and substring in name:
                continue
            if child not in children:
                children.append(child)
                graph.setdefault(child, [])
        graph[node] = children
        stack.extend((child, depth + 1) for child in reversed(children))
    return graph
