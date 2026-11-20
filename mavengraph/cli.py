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
    args = parser.parse_args(argv)
    try:
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
        repository = TestRepository(args.repository) if args.test_mode else MavenRepository(args.repository)
        for dependency in repository.dependencies(args.package):
            print(dependency)
    except (ValueError, OSError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1
    return 0
