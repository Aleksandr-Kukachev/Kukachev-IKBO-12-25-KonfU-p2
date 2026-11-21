import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

FIRST_PRINTABLE_CODE = 32


def coordinate(value):
    if not re.fullmatch(
        r"[A-Za-z0-9_][A-Za-z0-9_.-]*:"
        r"[A-Za-z0-9_][A-Za-z0-9_.-]*:"
        r"[A-Za-z0-9_][A-Za-z0-9_.+-]*",
        value,
    ):
        raise ValueError(
            "пакет Maven должен иметь вид groupId:artifactId:version"
            " (фиксированная версия)"
        )
    return value


def make_parser():
    parser = argparse.ArgumentParser(description="Граф зависимостей Maven")
    parser.add_argument(
        "--package",
        required=True,
        help="groupId:artifactId:version; в тестовом режиме A, B, ...",
    )
    parser.add_argument(
        "--repository",
        required=True,
        help="HTTP(S) URL или путь к тестовому JSON",
    )
    parser.add_argument(
        "--test-mode", action="store_true", help="читать тестовый JSON"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=10,
        help="число ребер от корня; 0 — только корень",
    )
    add_output_arguments(parser)
    return parser


def add_output_arguments(parser):
    """Добавить параметры фильтрации и вывода."""
    parser.add_argument(
        "--filter",
        default="",
        help="исключить имена с подстрокой, регистр учитывается",
    )
    parser.add_argument(
        "--mode",
        choices=("config", "direct", "graph", "order", "dot", "image"),
        default="graph",
    )
    parser.add_argument(
        "--output",
        default="build/graph.svg",
        help="путь к SVG/PNG для режима image",
    )
    parser.add_argument(
        "--dot", default="dot", help="путь к исполняемому файлу Graphviz"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="открыть изображение в просмотрщике",
    )


def options(argv=None):
    """Разобрать и проверить аргументы."""
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        validate_options(args)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    return args


def validate_output(args):
    """Проверить формат изображения и режим просмотра."""
    if args.show and args.mode != "image":
        raise ValueError("--show применяется только с --mode image")
    if args.mode == "image":
        if Path(args.output).suffix.lower() not in (".svg", ".png"):
            raise ValueError("--output должен иметь расширение .svg или .png")


def validate_repository(args):
    """Проверить источник данных и имя корневого пакета."""
    if args.test_mode:
        if not re.fullmatch("[A-Z]+", args.package):
            raise ValueError(
                "тестовое имя должно состоять из больших латинских букв"
            )
        if not Path(args.repository).is_file():
            raise ValueError("файл тестового репозитория не найден")
        return
    coordinate(args.package)
    url = urlsplit(args.repository)
    forbidden = (url.username, url.password, url.query, url.fragment)
    if (
        url.scheme not in ("http", "https")
        or not url.hostname
        or any(forbidden)
    ):
        raise ValueError(
            "репозиторий: нужен HTTP(S) URL без учетных данных, query и"
            " fragment"
        )
    _ = url.port
    if any(c.isspace() for c in args.repository):
        raise ValueError("URL не должен содержать пробелы")


def validate_options(args):
    """Проверить ограничения командной строки."""
    validate_output(args)
    validate_repository(args)
    if args.max_depth < 0:
        raise ValueError("максимальная глубина должна быть неотрицательной")
    if any(ord(c) < FIRST_PRINTABLE_CODE for c in args.filter):
        raise ValueError("фильтр не должен содержать управляющие символы")
    name = args.package if args.test_mode else args.package.split(":")[1]
    if args.filter and args.filter in name:
        raise ValueError("фильтр исключает анализируемый корневой пакет")


def print_graph(args, repository):
    """Построить граф и вывести его в выбранном формате."""
    import json
    from .graph import build_graph, loading_order
    from .visualize import render, to_dot

    graph = build_graph(repository, args.package, args.max_depth, args.filter)
    if args.mode == "order":
        print("\n".join(loading_order(graph)))
    elif args.mode == "dot":
        print(to_dot(graph, args.package), end="")
    elif args.mode == "image":
        print(render(graph, args.package, args.output, args.dot, args.show))
    else:
        print(json.dumps(graph, indent=2, ensure_ascii=False))


def run(args):
    """Выполнить выбранную операцию."""
    from .repository import MavenRepository, TestRepository

    if args.mode == "config":
        for key, value in vars(args).items():
            print(f"{key}={value}")
        return
    factory = TestRepository if args.test_mode else MavenRepository
    repository = factory(args.repository)
    if args.test_mode and args.package not in repository.graph:
        raise ValueError(
            f"пакет {args.package} отсутствует в тестовом репозитории"
        )
    if args.mode == "direct":
        kwargs = {} if args.test_mode else {"include_all": True}
        for dependency in repository.dependencies(args.package, **kwargs):
            print(dependency)
    else:
        print_graph(args, repository)


def main(argv=None):
    """Вернуть код завершения командной строки."""
    args = options(argv)
    try:
        run(args)
    except (ValueError, OSError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    return 0
