"""Примеры запуска на тестовых графах. Запускать из папки проекта."""

import subprocess
import sys
from pathlib import Path

CASES = [
    ["--mode", "config"],
    ["--repository", "examples/cycle.json"],
    ["--repository", "examples/self-loop.json"],
    ["--repository", "examples/isolated.json"],
    ["--max-depth", "0"],
    ["--max-depth", "1"],
    ["--filter", "B"],
    ["--repository", "examples/shorter-path.json", "--max-depth", "3"],
    ["--mode", "order"],
    ["--repository", "examples/cycle.json", "--mode", "order"],
    ["--repository", "examples/isolated.json", "--mode", "order"],
    ["--max-depth", "-1"],
    ["--max-depth", "bad"],
    ["--package", "a"],
    ["--repository", "missing.json"],
    ["--test-mode=true"],
    ["--filter", "A"],
    ["--filter", "\n"],
]


def run_case(args):
    """Запустить пример и собрать вывод процесса."""
    result = subprocess.run(
        [sys.executable, "-m", "mavengraph", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [
        "> python -m mavengraph " + subprocess.list2cmdline(args),
        f"exit={result.returncode}",
        result.stdout,
        result.stderr,
    ]


def main():
    lines = []
    for extra in CASES:
        args = [
            "--test-mode",
            "--package",
            "A",
            "--repository",
            "examples/diamond.json",
        ] + extra
        lines.extend(run_case(args))
    for extra in (
        ["--package", "invalid"],
        ["--repository", "ftp://example.org"],
        ["--repository", "https://example.org:bad"],
    ):
        args = [
            "--package",
            "junit:junit:4.13.2",
            "--repository",
            "https://repo.maven.apache.org/maven2",
            "--mode",
            "config",
        ] + extra
        lines.extend(run_case(args))
    Path("reports").mkdir(exist_ok=True)
    Path("reports/demo.txt").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
