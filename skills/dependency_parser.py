import io
from packaging.requirements import Requirement
from packaging.version import Version


class DependencyParser:
    """Парсер строк зависимостей для извлечения имени, версий, маркеров и экстр."""

    def parse(self, dependency_string: str) -> dict:
        if not isinstance(dependency_string, str) or not dependency_string.strip():
            raise ValueError("Empty or invalid dependency string")

        try:
            req = Requirement(dependency_string.strip())
        except Exception as e:
            raise ValueError(f"Malformed dependency string: {dependency_string}") from e

        version_constraint = str(req.specifier) if req.specifier else None

        return {
            "name": req.name,
            "version_constraint": version_constraint,
            "version": version_constraint,
            "marker": str(req.marker) if req.marker else None,
            "extras": list(req.extras) if req.extras else []
        }

    def parse_stream(self, stream: io.IOBase) -> list:
        results = []
        for line in stream:
            if isinstance(line, bytes):
                line_str = line.decode('utf-8', errors='ignore')
            else:
                line_str = str(line)

            line_str = line_str.strip()
            if not line_str or line_str.startswith("#"):
                continue

            try:
                parsed = self.parse(line_str)
                results.append(parsed)
            except Exception:
                continue
        return results

    def parse_batch(self, dependency_strings: list) -> list:
        return [self.parse(dep) for dep in dependency_strings]


def parse_dependency_string(dependency_string: str) -> dict:
    parser = DependencyParser()
    return parser.parse(dependency_string)