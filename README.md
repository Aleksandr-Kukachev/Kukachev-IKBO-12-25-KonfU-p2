# Maven Graph

Учебный CLI на Python 3.10+. Получение зависимостей — только стандартная библиотека Python, без Maven и сторонних библиотек.

## Этап 1

`python -m mavengraph --package junit:junit:4.13.2 --repository https://repo.maven.apache.org/maven2 --max-depth 3`

Параметры: `--package`, `--repository`, `--test-mode`, `--max-depth`, `--filter`.
Глубина — количество ребер от корня. Пустой фильтр выключен, непустой исключает artifactId с подстрокой с учетом регистра. Исключение корня — ошибка.

Проверка: `python -m unittest discover -s tests -v`.
Ошибки параметров возвращают код 2 и понятное сообщение в stderr. Проверяются координаты/тестовые имена, URL/файл, флаг режима, целая неотрицательная глубина и фильтр.

## Этап 2

Приложение читает POM по пути `groupId/artifactId/version/artifactId-version.pom`, разбирает XML, parent, свойства и dependencyManagement (включая BOM imports). Выводит прямые compile/runtime зависимости, исключая optional. Данные кэшируются в памяти. Ошибки сети, XML, отсутствующих версий и циклов parent/BOM возвращают код 1.
