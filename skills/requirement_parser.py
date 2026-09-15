import io
import re

try:
    from packaging.requirements import Requirement, InvalidRequirement
    from packaging.specifiers import SpecifierSet
    HAS_PACKAGING = True
except (ImportError, ModuleNotFoundError):
    HAS_PACKAGING = False
    Requirement = None
    InvalidRequirement = Exception
    SpecifierSet = None


class _FallbackSpecifier:
    def __init__(self, operator: str, version: str):
        self.operator = operator
        self.version = version

    def __str__(self):
        return f"{self.operator}{self.version}"


class _FallbackRequirement:
    def __init__(self, req_str: str):
        s = req_str.strip()
        if not s:
            raise ValueError("Empty requirement string")

        if ';' in s:
            req_part, marker_part = s.split(';', 1)
            self.marker = marker_part.strip() or None
        else:
            req_part = s
            self.marker = None

        req_part = req_part.strip()

        name_extra_pattern = r'^([a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?)(?:\s*\[([^\]]*)\])?\s*(.*)$'
        match = re.match(name_extra_pattern, req_part)
        if not match:
            raise ValueError(f"Invalid requirement format: {req_str}")

        self.name = match.group(1)
        extras_raw = match.group(2)
        specs_raw = match.group(3).strip()

        if extras_raw is not None:
            self.extras = set(e.strip() for e in extras_raw.split(',') if e.strip())
        else:
            self.extras = set()

        self.specifier = []
        if specs_raw:
            spec_pattern = r'^\s*(~=|===|==|!=|<=|>=|<|>)\s*([^\s,;]+)'
            remaining = specs_raw
            while remaining:
                m_spec = re.match(spec_pattern, remaining)
                if not m_spec:
                    raise ValueError(f"Invalid specifier in requirement: {specs_raw}")
                op = m_spec.group(1)
                ver = m_spec.group(2)
                self.specifier.append(_FallbackSpecifier(op, ver))
                remaining = remaining[m_spec.end():].strip()
                if remaining.startswith(','):
                    remaining = remaining[1:].strip()
                elif remaining:
                    raise ValueError(f"Invalid character after specifier: {remaining}")


class RequirementParser:
    def parse(self, req_string: str) -> dict:
        try:
            if HAS_PACKAGING:
                req = Requirement(req_string.strip())
            else:
                req = _FallbackRequirement(req_string.strip())
        except Exception as e:
            raise Exception(f"Invalid requirement: {e}")

        specs = []
        version = None
        if req.specifier:
            specs = [str(s) for s in req.specifier]
            for s in req.specifier:
                if getattr(s, 'operator', None) in ('==', '===', '>='):
                    version = s.version
                    break
            if not version and req.specifier:
                version = list(req.specifier)[0].version

        return {
            "name": req.name,
            "specs": specs,
            "version": version,
            "marker": str(req.marker) if req.marker else None,
            "extras": list(req.extras) if req.extras else []
        }

    def parse_line(self, line: str) -> dict:
        return self.parse(line)

    def parse_stream(self, stream: io.BytesIO) -> list:
        results = []
        content = stream.read().decode("utf-8")
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parsed = self.parse(line)
            results.append(parsed)
        return results


def parse_requirements(req_string: str):
    parser = RequirementParser()
    return [parser.parse(req_string)]
