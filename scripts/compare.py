"""Сравнение графа приложения с выводом Maven."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mavengraph.repository import MavenRepository
from mavengraph.graph import build_graph, loading_order

PACKAGES = ['junit:junit:4.13.2', 'org.apache.commons:commons-text:1.12.0',
            'com.fasterxml.jackson.core:jackson-databind:2.17.2']


def portable_log(text):
    root = Path(__file__).resolve().parents[1]
    return text.replace(str(root), '<project>').replace(root.as_posix(), '<project>')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mvn', default='mvn')
    args = parser.parse_args()
    base = Path('reports/real').resolve()
    base.mkdir(parents=True, exist_ok=True)
    cache = Path('build/maven-cache').resolve()
    for package in PACKAGES:
        group, artifact, version = package.split(':')
        dest = base / artifact
        dest.mkdir(exist_ok=True)
        graph = build_graph(MavenRepository('https://repo.maven.apache.org/maven2'), package, 10)
        (dest / 'graph.json').write_text(json.dumps(graph, indent=2), encoding='utf-8')
        (dest / 'order.txt').write_text('\n'.join(loading_order(graph)) + '\n', encoding='utf-8')
        (dest / 'pom.xml').write_text(f'<project xmlns="http://maven.apache.org/POM/4.0.0"><modelVersion>4.0.0</modelVersion><groupId>demo</groupId><artifactId>comparison</artifactId><version>1</version><dependencies><dependency><groupId>{group}</groupId><artifactId>{artifact}</artifactId><version>{version}</version></dependency></dependencies></project>', encoding='utf-8')
        common = [args.mvn, '-B', '-ntp', f'-Dmaven.repo.local={cache}', '-f', str(dest / 'pom.xml')]
        commands = [(['org.apache.maven.plugins:maven-dependency-plugin:3.8.1:resolve'], 'resolve.log'),
                    (['org.apache.maven.plugins:maven-dependency-plugin:3.8.1:tree', '-Dscope=runtime', '-DoutputType=text', f'-DoutputFile={dest / "maven-tree.txt"}'], 'tree.log'),
                    (['org.apache.maven.plugins:maven-dependency-plugin:3.8.1:tree', '-Dscope=runtime', '-DoutputType=dot', f'-DoutputFile={dest / "maven.dot"}'], 'dot.log')]
        for flags, log in commands:
            # Строки Downloaded нужны для сравнения порядка скачивания.
            command = [x for x in common if x != '-ntp'] + flags
            result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=240)
            (dest / log).write_text(portable_log(result.stdout + result.stderr), encoding='utf-8')
            if result.returncode:
                raise RuntimeError(f'Maven failed; see {dest / log}')
        tree = (dest / 'maven-tree.txt').read_text(encoding='utf-8')
        actual = {f'{g}:{a}:{v}' for g, a, v in re.findall(r'([\w.-]+):([\w.-]+):jar:([\w.+-]+):(?:compile|runtime)', tree)}
        comparison = {'package': package, 'our_nodes': sorted(graph), 'maven_nodes': sorted(actual),
                      'only_ours': sorted(set(graph) - actual), 'only_maven': sorted(actual - set(graph))}
        (dest / 'comparison.json').write_text(json.dumps(comparison, indent=2), encoding='utf-8')
        print(package, 'nodes=', len(graph), 'difference=', comparison['only_ours'], comparison['only_maven'], flush=True)


if __name__ == '__main__':
    main()
