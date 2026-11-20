"""Построение изображений по графам приложения и Maven."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mavengraph.visualize import render
from mavengraph.repository import TestRepository
from mavengraph.graph import build_graph


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dot', default='dot')
    args = parser.parse_args()
    for directory in sorted(Path('reports/real').iterdir()):
        graph = json.loads((directory / 'graph.json').read_text())
        root = next(iter(graph))
        for extension in ('svg', 'png'):
            render(graph, root, directory / f'graph.{extension}', args.dot)
            subprocess.run([args.dot, '-T' + extension, str(directory / 'maven.dot'), '-o', str(directory / f'maven.{extension}')], check=True)
        def normalize(node):
            parts = node.split(':')
            return ':'.join([parts[0], parts[1], parts[3]])
        maven_edges = {(normalize(a), normalize(b)) for a, b in re.findall(r'"([^"]+)"\s*->\s*"([^"]+)"', (directory / 'maven.dot').read_text()) if not a.startswith('demo:comparison:')}
        ours = {(a, b) for a, deps in graph.items() for b in deps}
        (directory / 'edge-comparison.json').write_text(json.dumps({'equal': ours == maven_edges, 'only_ours': sorted(ours - maven_edges), 'only_maven': sorted(maven_edges - ours)}, indent=2))
        print(directory.name, 'edges match:', ours == maven_edges)
    for source in sorted(Path('examples').glob('*.json')):
        graph = build_graph(TestRepository(source), 'A', 10)
        render(graph, 'A', Path('reports/test') / (source.stem + '.svg'), args.dot)


if __name__ == '__main__':
    main()
