import io
import re

try:
    from packaging.requirements import Requirement
except ImportError:
    class Requirement:  # type: ignore
        def __init__(self, requirement_string: str):
            if not requirement_string or not isinstance(requirement_string, str):
                raise ValueError("Invalid requirement string")

            if ";" in requirement_string:
                req_part, marker_part = requirement_string.split(";", 1)
                self.marker = marker_part.strip() or None
            else:
                req_part = requirement_string
                self.marker = None

            req_part = req_part.strip()

            pattern = r'^\s*([a-zA-Z0-9_\-\.]+)(?:\s*\[\s*([^\]]+)\s*\])?\s*(.*)$'
            match = re.match(pattern, req_part)
            if not match:
                raise ValueError(f"Invalid requirement string: {requirement_string}")

            name, extras_str, specifier_str = match.groups()

            # Validate specifiers if present: must match valid PEP 440 specifiers or direct references/parentheses
            if specifier_str:
                spec_clean = specifier_str.strip()
                # PEP 440 specifiers pattern or @ URL
                spec_pattern = r'^(?:(?:==|!=|<=|>=|~=|===|<|>|!=)\s*[a-zA-Z0-9_\-\.\*\+]+|\(.*\)|@\s*\S+)(?:\s*,\s*(?:==|!=|<=|>=|~=|===|<|>|!=)\s*[a-zA-Z0-9_\-\.\*\+]+)*$'
                if not re.match(spec_pattern, spec_clean):
                    raise ValueError(f"Invalid requirement string: {requirement_string}")
            match = re.match(pattern, req_part)
            if not match:
                raise ValueError(f"Invalid requirement string: {requirement_string}")

            name, extras_str, specifier_str = match.groups()
            self.name = name

            if extras_str:
                self.extras = {e.strip() for e in extras_str.split(",") if e.strip()}
            else:
                self.extras = set()

            specifier_str = specifier_str.strip() if specifier_str else ""
            if specifier_str.startswith("(") and specifier_str.endswith(")"):
                specifier_str = specifier_str[1:-1].strip()

            self.specifier = specifier_str if specifier_str else None


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