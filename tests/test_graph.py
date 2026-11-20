import unittest
from mavengraph.graph import build_graph


class MemoryRepository:
    def __init__(self, graph):
        self.graph = graph
        self.calls = []

    def dependencies(self, node):
        self.calls.append(node)
        return self.graph[node]


class GraphTests(unittest.TestCase):
    def test_shorter_path_reexpands_node(self):
        repo = MemoryRepository({'A': ['B', 'D'], 'B': ['C'], 'C': ['D'], 'D': ['E'], 'E': ['F'], 'F': []})
        graph = build_graph(repo, 'A', 3)
        self.assertEqual(graph['E'], ['F'])
        self.assertNotIn('F', repo.calls)

    def test_cycle_and_self_loop(self):
        repo = MemoryRepository({'A': ['A', 'B'], 'B': ['A']})
        self.assertEqual(build_graph(repo, 'A', 100), repo.graph)
        self.assertEqual(repo.calls, ['A', 'B'])

    def test_depth_and_filter(self):
        repo = MemoryRepository({'A': ['B', 'C'], 'B': ['D'], 'C': [], 'D': []})
        self.assertEqual(build_graph(repo, 'A', 0), {'A': []})
        self.assertEqual(build_graph(repo, 'A', 1, 'B'), {'A': ['C'], 'C': []})
        self.assertNotIn('B', repo.calls)

    def test_long_chain_without_recursion(self):
        source = {str(i): [str(i + 1)] for i in range(2000)}
        source['2000'] = []
        self.assertEqual(len(build_graph(MemoryRepository(source), '0', 3000)), 2001)
