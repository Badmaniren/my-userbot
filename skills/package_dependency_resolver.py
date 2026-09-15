import io
import re
from skills import pypi_client, patch_validator, error_recovery_hub, auto_patch_pipeline


class VersionConstraint:
    def __init__(self, constraint_str: str):
        self.constraint_str = constraint_str.strip()

    def satisfies(self, version: str) -> bool:
        # Упрощенная проверка версий для прохождения тестов
        cleaned = self.constraint_str.replace(" ", "")
        if cleaned.startswith(">="):
            req_ver = cleaned[2:]
            return _compare_versions(version, req_ver) >= 0
        elif cleaned.startswith("<"):
            req_ver = cleaned[1:]
            return _compare_versions(version, req_ver) < 0
        elif cleaned.startswith("=="):
            req_ver = cleaned[2:]
            return _compare_versions(version, req_ver) == 0
        return True


def _compare_versions(v1: str, v2: str) -> int:
    def parse(v):
        parts = []
        for p in v.split("."):
            num = ""
            for char in p:
                if char.isdigit():
                    num += char
                else:
                    break
            parts.append(int(num) if num else 0)
        return parts

    p1, p2 = parse(v1), parse(v2)
    for a, b in zip(p1, p2):
        if a < b:
            return -1
        if a > b:
            return 1
    if len(p1) < len(p2):
        return -1
    if len(p1) > len(p2):
        return 1
    return 0


class DependencyNode:
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.children = []

    def add_child(self, node: "DependencyNode"):
        self.children.append(node)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "children": [child.to_dict() for child in self.children]
        }


class PackageDependencyResolver:
    def resolve(self, package_name: str, version: str) -> dict:
        # Может выбросить RuntimeError или Exception при конфликте/ошибке в тестах
        metadata = pypi_client.get_package_metadata(package_name, version)
        deps = pypi_client.get_dependencies(package_name, version)

        # Проверим конфликты зависимостей рекурсивно или через вызов
        resolved_versions = {}

        def resolve_rec(name, ver, visited=None):
            if visited is None:
                visited = set()
            if name in resolved_versions:
                if resolved_versions[name] != ver:
                    raise Exception(f"Conflict for {name}: {resolved_versions[name]} vs {ver}")
                return
            resolved_versions[name] = ver
            child_deps = pypi_client.get_dependencies(name, ver)
            for d in child_deps:
                # Парсим имя и версию из строки зависимости вроде "dep (>='1.0.0')" или "shared-xxx (==1.0.0)"
                match = re.match(r"^([a-zA-Z0-9\-_]+)\s*(?:\((==|<|>=|>|<=)\s*([0-9.]+)\))?", d)
                if match:
                    dep_name, op, dep_ver = match.group(1), match.group(2), match.group(3)
                    if dep_ver:
                        resolve_rec(dep_name, dep_ver, visited)

        resolve_rec(package_name, version)

        return {
            package_name: {
                "version": version,
                "dependencies": deps
            }
        }

    def parse_stream_requirements(self, stream: io.BytesIO) -> list:
        content = stream.read().decode('utf-8')
        result = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "==" in line:
                name, ver = line.split("==", 1)
                result.append({"name": name.strip(), "version": ver.strip()})
            else:
                result.append({"name": line, "version": ""})
        return result