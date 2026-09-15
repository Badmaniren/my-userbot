import io
import re

class FallbackSpecifier:
    def __init__(self, operator, version):
        self.operator = operator
        self.version = version

class FallbackRequirement:
    def __init__(self, spec_str):
        spec_str = spec_str.strip()
        extras = []
        if '[' in spec_str and ']' in spec_str:
            match = re.search(r'^(.*?)\s*\[(.*?)\]\s*(.*)$', spec_str)
            if match:
                name_part, extras_part, spec_part = match.groups()
                extras = [e.strip() for e in extras_part.split(',') if e.strip()]
                spec_str = f"{name_part} {spec_part}".strip()

        match = re.match(r'^([A-Za-z0-9_.\-]+)\s*(.*)$', spec_str)
        if match:
            self.name = match.group(1)
            rest = match.group(2).strip()
        else:
            self.name = spec_str
            rest = ""

        self.extras = set(extras)
        self.specifier = []

        if rest:
            spec_match = re.match(r'^(==|>=|<=|>|<|~=|!=)\s*(.*)$', rest)
            if spec_match:
                op, ver = spec_match.groups()
                self.specifier.append(FallbackSpecifier(op, ver.strip()))

class FallbackSpecifierSet:
    def __init__(self, spec_str):
        self.spec_str = spec_str.strip()
        self.specifiers = []
        if self.spec_str:
            for part in self.spec_str.split(','):
                part = part.strip()
                spec_match = re.match(r'^(==|>=|<=|>|<|~=|!=)\s*(.*)$', part)
                if spec_match:
                    op, ver = spec_match.groups()
                    self.specifiers.append((op, ver.strip()))

    def _parse_version(self, v_str):
        parts = []
        for part in re.split(r'[\.\-\+]', str(v_str)):
            part = part.strip()
            if not part:
                continue
            if part.isdigit():
                parts.append((0, int(part)))
            else:
                parts.append((1, part))
        return tuple(parts)

    def __contains__(self, version_str):
        if not self.specifiers:
            return True
        target_v = self._parse_version(version_str)
        for op, ver in self.specifiers:
            spec_v = self._parse_version(ver)
            if op == "==":
                if target_v != spec_v:
                    return False
            elif op == "!=":
                if target_v == spec_v:
                    return False
            elif op == ">=":
                if target_v < spec_v:
                    return False
            elif op == "<=":
                if target_v > spec_v:
                    return False
            elif op == ">":
                if target_v <= spec_v:
                    return False
            elif op == "<":
                if target_v >= spec_v:
                    return False
            elif op == "~=":
                if target_v < spec_v:
                    return False
                if len(spec_v) > 1 and target_v[:len(spec_v)-1] != spec_v[:len(spec_v)-1]:
                    return False
        return True

try:
    from packaging.requirements import Requirement
    from packaging.specifiers import SpecifierSet
except ImportError:
    Requirement = FallbackRequirement
    SpecifierSet = FallbackSpecifierSet


class PEP508Specifier:
    """Вспомогательный класс для представления PEP 508 спецификатора."""
    def __init__(self, name, operator, version, extras=None):
        self.name = name
        self.operator = operator
        self.version = version
        self.extras = extras or []

    def get(self, key, default=None):
        if key == "name":
            return self.name
        if key == "operator":
            return self.operator
        if key == "version":
            return self.version
        if key == "extras":
            return self.extras
        return default


class RequirementAnalyzer:
    """Анализатор требований и спецификаций версий пакетов (PEP 508)."""

    def __init__(self, raw_spec=None):
        self.name = None
        self.operator = None
        self.version = None
        self.extras = []

        if raw_spec:
            parsed = self._parse_single(raw_spec)
            self.name = parsed.name
            self.operator = parsed.operator
            self.version = parsed.version
            self.extras = parsed.extras

    def _parse_single(self, spec_str):
        req = Requirement(spec_str)
        name = req.name
        extras = list(req.extras)
        spec_list = list(req.specifier)
        if spec_list:
            operator = spec_list[0].operator
            version = spec_list[0].version
        else:
            operator = "=="
            version = ""
        return PEP508Specifier(name, operator, version, extras)

    def match(self, version_str):
        if not self.operator or not self.version:
            return True
        spec_str = f"{self.operator}{self.version}"
        spec_set = SpecifierSet(spec_str)
        return version_str in spec_set

    def parse(self, spec_str):
        parsed = self._parse_single(spec_str)
        return [parsed]

    def parse_stream(self, stream):
        if isinstance(stream, io.BytesIO):
            content = stream.read().decode('utf-8')
        elif isinstance(stream, io.StringIO):
            content = stream.read()
        else:
            content = str(stream)

        results = []
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                results.append(self._parse_single(line))
        return results
