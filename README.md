# Maven Graph

Учебный CLI на Python 3.10+. Получение зависимостей — только стандартная библиотека Python, без Maven и сторонних библиотек.

## Этап 1

`python -m mavengraph --package junit:junit:4.13.2 --repository https://repo.maven.apache.org/maven2 --max-depth 3`

Параметры: `--package`, `--repository`, `--test-mode`, `--max-depth`, `--filter`.
Глубина — количество ребер от корня. Пустой фильтр выключен, непустой исключает artifactId с подстрокой с учетом регистра. Исключение корня — ошибка.

Проверка: `python -m unittest discover -s tests -v`.
Ошибки параметров возвращают код 2 и понятное сообщение в stderr. Проверяются координаты/тестовые имена, URL/файл, флаг режима, целая неотрицательная глубина и фильтр.

## Этап 2

Приложение читает POM по пути `groupId/artifactId/version/artifactId-version.pom`, разбирает XML, parent, свойства и dependencyManagement (включая BOM imports). В окончательной версии режим direct выводит все объявленные прямые зависимости, включая test/provided/optional; режимы графа используют compile/runtime без optional. Данные кэшируются в памяти. Ошибки сети, XML, отсутствующих версий и циклов parent/BOM возвращают код 1.

## Этап 3

`python -m mavengraph --test-mode --package A --repository examples/diamond.json --max-depth 3`

JSON содержит объект `{ "A": ["B"], "B": [] }`. Каждая ссылка должна иметь запись, имена состоят из A–Z. Примеры: diamond, cycle, self-loop, isolated, shorter-path. Обход выполняется DFS с явным стеком. Вершина повторно раскрывается при обнаружении более короткого пути: результат не зависит от того, какая ветка DFS посещена первой. На границе глубины POM не запрашивается. Циклы сохраняются в графе, но не вызывают бесконечного обхода.

В окончательном CLI режимы `--mode config` и `--mode direct` воспроизводят вывод этапов 1 и 2. По умолчанию выводится JSON графа. В direct глубина и фильтр не применяются: это диагностический вывод всех поддерживаемых прямых зависимостей.

## Этап 4

`python -m mavengraph --test-mode --package A --repository examples/diamond.json --mode order`

Порядок D, B, C, A: зависимости раньше потребителей, корень последний. Это обратный топологический порядок, вычисляемый итеративным DFS. Для цикла линейный порядок невозможен: программа сообщает путь цикла и код 1. При ограничении глубины порядок относится только к построенному графу.

`python scripts/demo.py` записывает воспроизводимую демонстрацию разных тестовых графов, глубины, фильтра и ошибок в `reports/demo.txt`.

## Этап 5 — запуск и изображения

```powershell
# В этой папке на текущем компьютере можно использовать .\run.ps1 вместо python -m mavengraph
.\run.ps1 --test-mode --package A --repository examples/cycle.json --mode image --output build/cycle.svg --show
.\run.ps1 --package junit:junit:4.13.2 --repository https://repo.maven.apache.org/maven2 --mode image --output build/junit.png --show
```

Для переноса проекта нужны Python 3.10+ и [Graphviz](https://graphviz.org/download/). Python-пакеты устанавливать не требуется. Graphviz используется только для рисования готового DOT. `--dot` задает путь к dot, `--output` — SVG/PNG, `--show` открывает файл в браузере/просмотрщике. Без `--show` создается файл. `--mode dot` выводит DOT в stdout и не требует Graphviz. Если Graphviz отсутствует, DOT сохраняется рядом с запрошенным изображением, программа объясняет ошибку и возвращает 1.

В `reports/real` находятся готовые PNG/SVG для **JUnit 4.13.2**, **Commons Text 1.12.0**, **Jackson Databind 2.17.2**: `graph.*` — наш результат, `maven.*` — штатный DOT Maven, отрисованный тем же Graphviz. В `reports/test` — пять тестовых графов. Стрелка A → B означает «A зависит от B», зеленый узел — корень.

## Проверка и сравнение

```text
python -m unittest discover -s tests -v
python scripts/demo.py
python scripts/compare.py --mvn /path/to/mvn
python scripts/render_examples.py --dot /path/to/dot
```

Для compare требуется JDK и Maven. Он используется исключительно отдельным скриптом сравнения; приложение Maven не вызывает. Скрипт сохраняет реальные stdout/stderr Maven и использует отдельный локальный кэш `build/maven-cache`. Сетевой порядок при повторном запуске может отсутствовать из-за кэша. Подробности и наблюдаемые расхождения: [REPORT.md](REPORT.md).

## Границы модели Maven

Это учебный анализатор объявленного графа, а не полная реализация Maven Resolver. Поддержаны фиксированные release-версии, обычные parent и BOM, свойства и compile/runtime-зависимости. Не реализованы профили, exclusions, разрешение конфликтов версий по nearest-wins, перенос управления версиями корня на весь транзитивный граф, classifiers/types как разные вершины, relocation, repositories внутри POM, Maven settings и timestamped SNAPSHOT metadata. Диапазоны и неразрешенные свойства вызывают ошибку. Сложные правила наследования effective POM/BOM могут отличаться от Maven. Эти ограничения способны дать лишние вершины или иные версии; совпадение на трех примерах не означает полной совместимости с Maven.

При `--max-depth 0` реальный репозиторий не запрашивается, поэтому существование Maven-пакета не проверяется. В тестовом режиме весь JSON проверяется до обхода. Фильтр регистрозависим и применяется к artifactId (к полному буквенному имени в тестовом режиме), исключая всю соответствующую ветку, если к потомкам нет другого пути.

## История этапов

Каждый этап оформлен отдельным Conventional Commit (`git log --oneline --reverse`). Первые два состояния показывают специальный вывод своих этапов; итоговое приложение сохраняет этот функционал в режимах config и direct.
