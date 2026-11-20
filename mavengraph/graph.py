"""Обход графа с учетом глубины."""


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


def loading_order(graph):
    """Зависимости выводятся раньше потребителя. Для цикла порядка нет."""
    colors, result = {}, []
    for start in graph:
        if colors.get(start):
            continue
        colors[start] = 1
        path = [start]
        stack = [(start, iter(graph[start]))]
        while stack:
            node, children = stack[-1]
            child = next(children, None)
            if child is None:
                colors[node] = 2
                result.append(node)
                stack.pop(); path.pop()
            elif colors.get(child) == 1:
                cycle = path[path.index(child):] + [child]
                raise ValueError("порядок загрузки невозможен: цикл " + " -> ".join(cycle))
            elif not colors.get(child):
                colors[child] = 1
                path.append(child)
                stack.append((child, iter(graph[child])))
    return result
