"""Reproducible offline CLI demonstrations; run from the repository root."""
import subprocess
import sys
from pathlib import Path


def main():
    cases = [
        ['--mode', 'config'],
        ['--repository', 'examples/cycle.json'],
        ['--repository', 'examples/self-loop.json'],
        ['--repository', 'examples/isolated.json'],
        ['--max-depth', '0'], ['--max-depth', '1'], ['--filter', 'B'],
        ['--repository', 'examples/shorter-path.json', '--max-depth', '3'],
        ['--mode', 'order'],
        ['--repository', 'examples/cycle.json', '--mode', 'order'],
        ['--repository', 'examples/isolated.json', '--mode', 'order'],
        ['--max-depth', '-1'], ['--max-depth', 'bad'], ['--package', 'a'],
        ['--repository', 'missing.json'], ['--test-mode=true'], ['--filter', 'A'],
        ['--filter', '\n'],
    ]
    lines = []
    for extra in cases:
        args = ['--test-mode', '--package', 'A', '--repository', 'examples/diamond.json'] + extra
        result = subprocess.run([sys.executable, '-m', 'mavengraph', *args], capture_output=True, text=True, encoding='utf-8')
        lines.extend(['> python -m mavengraph ' + subprocess.list2cmdline(args),
                      f'exit={result.returncode}', result.stdout, result.stderr])
    Path('reports').mkdir(exist_ok=True)
    Path('reports/demo.txt').write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    main()
