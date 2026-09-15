import io
import re
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet

class PEP508Specifier:
    """Вспомогательный класс для представления PEP 508 спецификатора."""
    def __init__(self, name, operator, version, extras=None):
        self.name = name
        self.operator = operator
        self.version = version
        self.extras = extras or []

    def get(self, key):
        if key == "name":
            return self.name
        return None

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