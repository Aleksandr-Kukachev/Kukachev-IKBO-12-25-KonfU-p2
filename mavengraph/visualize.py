import json
from pathlib import Path
import subprocess
import webbrowser


def to_dot(graph, root):
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    lines = ['digraph dependencies {', '  rankdir=LR;',
             '  graph [bgcolor="#f5f7fb", pad="0.4"];',
             '  node [shape=box, style="rounded,filled", fillcolor="#e0edff", fontname="Arial"];',
             '  edge [color="#64748b"];']
    for node in graph:
        style = ' [fillcolor="#99d9c8", penwidth=2]' if node == root else ''
        lines.append(f'  {quote(node)}{style};')
    for node, children in graph.items():
        for child in children:
            lines.append(f'  {quote(node)} -> {quote(child)};')
    return '\n'.join(lines + ['}', ''])


def render(graph, root, output, executable='dot', show=False):
    output = Path(output).resolve()
    if output.suffix.lower() not in ('.svg', '.png'):
        raise ValueError('изображение должно иметь расширение .svg или .png')
    output.parent.mkdir(parents=True, exist_ok=True)
    dot_file = output.with_suffix('.dot')
    dot_file.write_text(to_dot(graph, root), encoding='utf-8')
    try:
        result = subprocess.run([executable, '-T' + output.suffix[1:].lower(), str(dot_file), '-o', str(output)],
                                capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
    except FileNotFoundError as exc:
        raise ValueError(f'Graphviz dot не найден. Установите Graphviz или укажите --dot. DOT сохранен: {dot_file}') from exc
    except subprocess.TimeoutExpired as exc:
        raise ValueError('Graphviz не завершился за 60 секунд') from exc
    if result.returncode:
        raise ValueError('Graphviz: ' + result.stderr.strip())
    if show and not webbrowser.open(output.as_uri()):
        raise ValueError(f'не удалось открыть просмотрщик; откройте изображение: {output}')
    return output
