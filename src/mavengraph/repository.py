"""Чтение Maven POM и тестового репозитория."""

import json
import re
import xml.etree.ElementTree as element_tree
from pathlib import Path
from urllib.request import Request, urlopen
from .cli import coordinate

MAX_PARENT_DEPTH = 100
MAX_POM_BYTES = 4 * 1024 * 1024
COORDINATE_KEYS = ("groupId", "artifactId", "version")


class RepositoryError(ValueError):
    pass


def expand(text, properties):
    for _ in range(50):
        updated = re.sub(
            r"\$\{([^}]+)\}", lambda m: properties.get(m[1], m[0]), text
        )
        if updated == text:
            break
        text = updated
    if "${" in text:
        raise RepositoryError(
            f"неразрешенное или циклическое свойство: {text}"
        )
    return text


class MavenRepository:
    def __init__(self, url, fetch=None):
        self.url = url.rstrip("/")
        self.fetch = fetch or self.download
        self.cache = {}
        self.active = set()

    def download(self, url):
        try:
            with urlopen(
                Request(url, headers={"User-Agent": "MavenGraph/1.0"}),
                timeout=20,
            ) as response:
                data = response.read(MAX_POM_BYTES + 1)
                if len(data) > MAX_POM_BYTES:
                    raise RepositoryError("POM превышает 4 MiB")
                return data
        except (OSError, ValueError) as exc:
            raise RepositoryError(
                f"не удалось загрузить {url}: {exc}"
            ) from exc

    def model(self, package):
        if package in self.cache:
            return self.cache[package]
        if package in self.active or len(self.active) >= MAX_PARENT_DEPTH:
            raise RepositoryError(
                f"цикл или слишком глубокая цепочка parent/BOM: {package}"
            )
        coordinate(package)
        self.active.add(package)
        try:
            root = self.read_project(package)
            props, management, inherited = self.parent_model(root)
            update_properties(root, package, props)
            self.update_management(root, props, management)
            declared = inherited + records(root, "dependencies/dependency")
            result = props, management, declared
            self.cache[package] = result
            return result
        finally:
            self.active.remove(package)

    def read_project(self, package):
        """Загрузить POM, проверить XML и убрать пространства имен."""
        group, artifact, version = package.split(":")
        directory = (
            f"{self.url}/{group.replace('.', '/')}/{artifact}/{version}"
        )
        data = self.fetch(f"{directory}/{artifact}-{version}.pom")
        if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():
            raise RepositoryError("DTD и XML entities не поддерживаются")
        try:
            root = element_tree.fromstring(data)
        except element_tree.ParseError as exc:
            raise RepositoryError(
                f"некорректный XML {package}: {exc}"
            ) from exc
        for node in root.iter():
            node.tag = node.tag.rsplit("}", 1)[-1]
        if root.tag != "project":
            raise RepositoryError(f"ожидался Maven project: {package}")
        return root

    def parent_model(self, root):
        """Скопировать данные родителя, не меняя его кеш."""
        parent = root.find("parent")
        if parent is None:
            return {}, {}, []
        parent_id = ":".join(
            (parent.findtext(key) or "").strip() for key in COORDINATE_KEYS
        )
        parent_props, parent_management, inherited = self.model(parent_id)
        props = dict(parent_props)
        for key, value in zip(COORDINATE_KEYS, parent_id.split(":")):
            props[f"project.parent.{key}"] = value
            props[f"parent.{key}"] = value
        return props, dict(parent_management), list(inherited)

    def update_management(self, root, props, management):
        """Добавить локальные управляемые зависимости и импортируемые BOM."""
        for dep in records(
            root, "dependencyManagement/dependencies/dependency"
        ):
            dep = {key: expand(value, props) for key, value in dep.items()}
            if dep.get("scope") == "import" and dep.get("type") == "pom":
                bom = ":".join(dep.get(key, "") for key in COORDINATE_KEYS)
                for key, value in self.model(bom)[1].items():
                    management.setdefault(key, value)
            else:
                management[(dep.get("groupId"), dep.get("artifactId"))] = dep

    def dependencies(self, package, include_all=False):
        props, management, declared = self.model(package)
        merged = {}
        for raw in declared:
            dep = {k: expand(v, props) for k, v in raw.items()}
            key = (dep.get("groupId"), dep.get("artifactId"))
            effective = dict(management.get(key, {}))
            effective.update(dep)
            merged[key] = effective
        result = []
        for dep in merged.values():
            if not include_all and (
                dep.get("scope", "compile") not in ("compile", "runtime")
                or dep.get("optional") == "true"
            ):
                continue
            target = ":".join(
                expand(dep.get(k, ""), props)
                for k in ("groupId", "artifactId", "version")
            )
            try:
                coordinate(target)
            except ValueError as exc:
                raise RepositoryError(
                    f"{package}: неподдерживаемая зависимость {target}: {exc}"
                ) from exc
            if target not in result:
                result.append(target)
        return result


def records(root, path):
    """Прочитать поля зависимостей без блока exclusions."""
    return [
        {
            node.tag: (node.text or "").strip()
            for node in dep
            if node.tag != "exclusions"
        }
        for dep in root.findall(path)
    ]


def update_properties(root, package, props):
    """Добавить свойства текущего проекта поверх родительских."""
    property_node = root.find("properties")
    if property_node is not None:
        props.update(
            {node.tag: (node.text or "").strip() for node in property_node}
        )
    for prefix in ("project", "pom"):
        for key, value in zip(COORDINATE_KEYS, package.split(":")):
            props[f"{prefix}.{key}"] = value


class TestRepository:
    def __init__(self, path):
        try:
            self.graph = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise RepositoryError(f"не удалось прочитать JSON: {exc}") from exc
        if not isinstance(self.graph, dict):
            raise RepositoryError(
                "JSON должен быть объектом: имя -> список зависимостей"
            )
        for name, deps in self.graph.items():
            if not re.fullmatch("[A-Z]+", name) or not isinstance(deps, list):
                raise RepositoryError(f"некорректная запись: {name}")
            for dep in deps:
                if (
                    not isinstance(dep, str)
                    or not re.fullmatch("[A-Z]+", dep)
                    or dep not in self.graph
                ):
                    raise RepositoryError(
                        f"{name}: неизвестная или некорректная зависимость"
                        f" {dep!r}"
                    )

    def dependencies(self, package):
        if package not in self.graph:
            raise RepositoryError(
                f"пакет {package} отсутствует в тестовом репозитории"
            )
        return list(dict.fromkeys(self.graph[package]))
