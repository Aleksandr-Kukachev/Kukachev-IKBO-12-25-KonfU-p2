"""Сравнение графа приложения с выводом Maven."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from mavengraph.repository import MavenRepository
from mavengraph.graph import build_graph, loading_order

PACKAGES = [
    "junit:junit:4.13.2",
    "org.apache.commons:commons-text:1.12.0",
    "com.fasterxml.jackson.core:jackson-databind:2.17.2",
]


def portable_log(text):
    root = Path(__file__).resolve().parents[1]
    return text.replace(str(root), "<project>").replace(
        root.as_posix(), "<project>"
    )


PLUGIN = "org.apache.maven.plugins:maven-dependency-plugin:3.8.1"


def write_inputs(package, dest):
    """Сохранить граф, порядок загрузки и POM для Maven."""
    group, artifact, version = package.split(":")
    graph = build_graph(
        MavenRepository("https://repo.maven.apache.org/maven2"), package, 10
    )
    (dest / "graph.json").write_text(
        json.dumps(graph, indent=2), encoding="utf-8"
    )
    (dest / "order.txt").write_text(
        "\n".join(loading_order(graph)) + "\n", encoding="utf-8"
    )
    pom = (
        '<project xmlns="http://maven.apache.org/POM/4.0.0">'
        "<modelVersion>4.0.0</modelVersion><groupId>demo</groupId>"
        "<artifactId>comparison</artifactId><version>1</version>"
        "<dependencies><dependency>"
        f"<groupId>{group}</groupId><artifactId>{artifact}</artifactId>"
        f"<version>{version}</version>"
        "</dependency></dependencies></project>"
    )
    (dest / "pom.xml").write_text(pom, encoding="utf-8")
    return graph


def maven_commands(dest):
    """Сформировать команды разрешения и вывода дерева."""
    return [
        ([PLUGIN + ":resolve"], "resolve.log"),
        (
            [
                PLUGIN + ":tree",
                "-Dscope=runtime",
                "-DoutputType=text",
                f'-DoutputFile={dest / "maven-tree.txt"}',
            ],
            "tree.log",
        ),
        (
            [
                PLUGIN + ":tree",
                "-Dscope=runtime",
                "-DoutputType=dot",
                f'-DoutputFile={dest / "maven.dot"}',
            ],
            "dot.log",
        ),
    ]


def run_maven(mvn, dest, cache):
    """Запустить Maven со строками Downloaded для сравнения порядка."""
    common = [
        mvn,
        "-B",
        f"-Dmaven.repo.local={cache}",
        "-f",
        str(dest / "pom.xml"),
    ]
    for flags, log in maven_commands(dest):
        result = subprocess.run(
            common + flags,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=240,
        )
        (dest / log).write_text(
            portable_log(result.stdout + result.stderr), encoding="utf-8"
        )
        if result.returncode:
            raise RuntimeError(f"Maven failed; see {dest / log}")


def compare_nodes(package, dest, graph):
    """Сохранить различия в наборах узлов."""
    tree = (dest / "maven-tree.txt").read_text(encoding="utf-8")
    actual = {
        f"{g}:{a}:{v}"
        for g, a, v in re.findall(
            r"([\w.-]+):([\w.-]+):jar:([\w.+-]+):(?:compile|runtime)", tree
        )
    }
    comparison = {
        "package": package,
        "our_nodes": sorted(graph),
        "maven_nodes": sorted(actual),
        "only_ours": sorted(set(graph) - actual),
        "only_maven": sorted(actual - set(graph)),
    }
    (dest / "comparison.json").write_text(
        json.dumps(comparison, indent=2), encoding="utf-8"
    )
    print(
        package,
        "nodes=",
        len(graph),
        "difference=",
        comparison["only_ours"],
        comparison["only_maven"],
        flush=True,
    )


def main():
    """Сравнить каждый пример с Maven."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--mvn", default="mvn")
    args = parser.parse_args()
    base = Path("reports/real").resolve()
    base.mkdir(parents=True, exist_ok=True)
    cache = Path("build/maven-cache").resolve()
    for package in PACKAGES:
        dest = base / package.split(":")[1]
        dest.mkdir(exist_ok=True)
        graph = write_inputs(package, dest)
        run_maven(args.mvn, dest, cache)
        compare_nodes(package, dest, graph)


if __name__ == "__main__":
    main()
