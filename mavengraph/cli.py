import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit


def coordinate(value):
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*:[A-Za-z0-9_][A-Za-z0-9_.-]*:[A-Za-z0-9_][A-Za-z0-9_.+-]*", value):
        raise ValueError("пакет Maven должен иметь вид groupId:artifactId:version (фиксированная версия)")
    return value


def options(argv=None):
    parser = argparse.ArgumentParser(description="Граф зависимостей Maven")
    parser.add_argument("--package", required=True, help="groupId:artifactId:version; в тестовом режиме A, B, ...")
    parser.add_argument("--repository", required=True, help="HTTP(S) URL или путь к тестовому JSON")
    parser.add_argument("--test-mode", action="store_true", help="читать тестовый JSON")
    parser.add_argument("--max-depth", type=int, default=10, help="число ребер от корня; 0 — только корень")
    parser.add_argument("--filter", default="", help="исключить имена с подстрокой, регистр учитывается")
    parser.add_argument("--mode", choices=("config", "direct", "graph", "order", "dot", "image"), default="graph")
    parser.add_argument("--output", default="build/graph.svg", help="путь к SVG/PNG для режима image")
    parser.add_argument("--dot", default="dot", help="путь к исполняемому файлу Graphviz")
    parser.add_argument("--show", action="store_true", help="открыть изображение в просмотрщике")
    args = parser.parse_args(argv)
    try:
        if args.show and args.mode != "image":
            raise ValueError("--show применяется только с --mode image")
        if args.mode == "image" and Path(args.output).suffix.lower() not in (".svg", ".png"):
            raise ValueError("--output должен иметь расширение .svg или .png")
        if args.test_mode:
            if not re.fullmatch("[A-Z]+", args.package):
                raise ValueError("тестовое имя должно состоять из больших латинских букв")
            if not Path(args.repository).is_file():
                raise ValueError("файл тестового репозитория не найден")
        else:
            coordinate(args.package)
            url = urlsplit(args.repository)
            if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password or url.query or url.fragment:
                raise ValueError("репозиторий: нужен HTTP(S) URL без учетных данных, query и fragment")
            _ = url.port
            if any(c.isspace() for c in args.repository):
                raise ValueError("URL не должен содержать пробелы")
        if args.max_depth < 0:
            raise ValueError("максимальная глубина должна быть неотрицательной")
        if any(ord(c) < 32 for c in args.filter):
            raise ValueError("фильтр не должен содержать управляющие символы")
        name = args.package if args.test_mode else args.package.split(":")[1]
        if args.filter and args.filter in name:
            raise ValueError("фильтр исключает анализируемый корневой пакет")
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    return args


def main(argv=None):
    args = options(argv)
    from .repository import MavenRepository, TestRepository
    try:
        if args.mode == "config":
            for key, value in vars(args).items():
                print(f"{key}={value}")
            return 0
        repository = TestRepository(args.repository) if args.test_mode else MavenRepository(args.repository)
        if args.test_mode and args.package not in repository.graph:
            raise ValueError(f"пакет {args.package} отсутствует в тестовом репозитории")
        if args.mode == "direct":
            direct = repository.dependencies(args.package) if args.test_mode else repository.dependencies(args.package, include_all=True)
            for dependency in direct:
                print(dependency)
        else:
            from .graph import build_graph
            import json
            graph = build_graph(repository, args.package, args.max_depth, args.filter)
            if args.mode == "order":
                from .graph import loading_order
                print("\n".join(loading_order(graph)))
            elif args.mode == "dot":
                from .visualize import to_dot
                print(to_dot(graph, args.package), end="")
            elif args.mode == "image":
                from .visualize import render
                print(render(graph, args.package, args.output, args.dot, args.show))
            else:
                print(json.dumps(graph, indent=2, ensure_ascii=False))
    except (ValueError, OSError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    return 0
