import re
import io

try:
    from packaging.requirements import Requirement, InvalidRequirement
except (ImportError, ModuleNotFoundError):
    class InvalidRequirement(ValueError):
        pass

    class _FallbackSpecifier:
        def __init__(self, operator: str, version: str):
            self.operator = operator
            self.version = version

        def __repr__(self):
            return f"{self.operator}{self.version}"

    class _FallbackRequirement:
        def __init__(self, raw_req: str):
            if not raw_req or not isinstance(raw_req, str):
                raise InvalidRequirement("Empty or non-string requirement")

            s = raw_req.strip()
            if not s:
                raise InvalidRequirement("Empty requirement")

            # Extract marker after ';'
            if ';' in s:
                s, marker_part = s.split(';', 1)
                self.marker = marker_part.strip() or None
            else:
                self.marker = None

            s = s.strip()

            # Extract extras in [...]
            extras = set()
            if '[' in s and ']' in s:
                match_extras = re.search(r'\[([^\]]+)\]', s)
                if match_extras:
                    extras_str = match_extras.group(1)
                    for e in extras_str.split(','):
                        e_clean = e.strip()
                        if e_clean:
                            extras.add(e_clean)
                    s = s[:match_extras.start()] + s[match_extras.end():]

            self.extras = extras

            # Clean parentheses
            if '(' in s and ')' in s:
                s = s.replace('(', ' ').replace(')', ' ').strip()

            s = s.strip()

            # Extract package name (PEP 508 name starts with alphanumeric character)
            name_match = re.match(r'^([a-zA-Z0-9][a-zA-Z0-9_.\-]*)\s*(.*)$', s)
            if not name_match:
                raise InvalidRequirement(f"Invalid dependency name: {raw_req}")

            name, rest = name_match.groups()
            self.name = name

            rest = rest.strip()
            specifiers = []
            if rest:
                # Multiple specifiers separated by comma
                parts = rest.split(',')
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    spec_match = re.match(r'^(==|>=|<=|>|<|!=|~=|===)\s*([a-zA-Z0-9_.\-+*!]+)$', part)
                    if not spec_match:
                        raise InvalidRequirement(f"Invalid specifier: {part}")
                    op, ver = spec_match.groups()
                    specifiers.append(_FallbackSpecifier(op, ver))

            self.specifier = specifiers

    Requirement = _FallbackRequirement


class DependencyParser:
    def parse(self, raw_req: str) -> dict:
        try:
            req = Requirement(raw_req)
        except (InvalidRequirement, ValueError) as e:
            raise ValueError(f"Invalid dependency string: {raw_req}") from e

        operator = None
        version = None
        if req.specifier:
            specs = list(req.specifier)
            if specs:
                operator = specs[0].operator
                version = specs[0].version

        return {
            'name': req.name,
            'operator': operator,
            'version': version,
            'extras': list(req.extras) if req.extras else [],
            'marker': str(req.marker) if req.marker else None
        }

    def parse_stream(self, stream: io.BytesIO) -> list:
        content = stream.read().decode('utf-8')
        results = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '#' in line:
                line = line.split('#', 1)[0].strip()
            try:
                results.append(self.parse(line))
            except ValueError:
                continue
        return results


def parse_dependency(raw_req: str):
    parser = DependencyParser()
    return parser.parse(raw_req)


def parse_dependency_string(raw_req: str):
    try:
        return parse_dependency(raw_req)
    except ValueError:
        return None
