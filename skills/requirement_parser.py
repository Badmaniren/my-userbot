import io
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Union

try:
    from packaging.requirements import Requirement, InvalidRequirement
    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False
    class InvalidRequirement(Exception):
        pass
    Requirement = None

from skills.pypi_client import PyPIClient

@dataclass
class ParsedRequirement:
    name: str
    version_specifier: str = ""
    extras: List[str] = field(default_factory=list)
    environment_markers: str = ""

    def get(self, key: str, default: Any = None) -> Any:
        if key == "name":
            return self.name
        elif key == "version":
            spec = self.version_specifier
            for op in ["==", ">=", "<=", ">", "<", "~=", "!="]:
                if spec.startswith(op):
                    return spec[len(op):].strip()
            return spec.strip() or default
        elif key == "extras":
            return self.extras
        elif key == "environment_markers":
            return self.environment_markers
        return default

def _normalize_req_string(req_string: str) -> str:
    s = req_string.strip()
    pattern = r'^([A-Za-z0-9_.-]+)\s*([<>=!~^][^;\[]+)\s*\[([^\]]+)\]\s*(;.*)?$'
    m = re.match(pattern, s)
    if m:
        pkg, spec, extras, marker = m.groups()
        res = f"{pkg}[{extras}]{spec}"
        if marker:
            res += f" {marker.strip()}"
        return res
    return s

class RequirementParser:
    def __init__(self, pypi_client: Any = None):
        self.pypi_client = pypi_client if pypi_client is not None else PyPIClient()

    def parse_requirement(self, req_string: str) -> ParsedRequirement:
        normalized_str = _normalize_req_string(req_string)
        if HAS_PACKAGING and Requirement is not None:
            try:
                req = Requirement(normalized_str)
                version_specifier = str(req.specifier) if req.specifier else ""
                env_markers = str(req.marker) if req.marker else ""

                return ParsedRequirement(
                    name=req.name,
                    version_specifier=version_specifier,
                    extras=list(req.extras),
                    environment_markers=env_markers
                )
            except InvalidRequirement as e:
                raise ValueError(f"Invalid requirement format: {req_string}") from e
            except Exception as e:
                raise ValueError(f"Invalid requirement format: {req_string}") from e

        return self._parse_requirement_fallback(req_string)

    def _parse_requirement_fallback(self, req_string: str) -> ParsedRequirement:
        s = req_string.strip()
        if not s:
            raise ValueError(f"Invalid requirement format: {req_string}")

        if '#' in s:
            s = s.split('#')[0].strip()

        env_markers = ""
        if ';' in s:
            s, env_markers = s.split(';', 1)
            s = s.strip()
            env_markers = env_markers.strip()

        m_name = re.match(r'^([A-Za-z0-9_.-]+)(.*)$', s)
        if not m_name:
            raise ValueError(f"Invalid requirement format: {req_string}")

        name = m_name.group(1)
        rest = m_name.group(2).strip()

        extras = []
        extras_match = re.search(r'\[([^\]]+)\]', rest)
        if extras_match:
            extras = [e.strip() for e in extras_match.group(1).split(',') if e.strip()]
            rest = (rest[:extras_match.start()] + rest[extras_match.end():]).strip()

        if rest.startswith('(') and rest.endswith(')'):
            rest = rest[1:-1].strip()

        version_specifier = rest

        if version_specifier and not re.match(r'^[<>=!~^]', version_specifier):
            raise ValueError(f"Invalid requirement format: {req_string}")

        return ParsedRequirement(
            name=name,
            version_specifier=version_specifier,
            extras=extras,
            environment_markers=env_markers
        )

    def parse_stream(self, stream: io.BytesIO) -> List[ParsedRequirement]:
        content = stream.read().decode('utf-8')
        results = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '#' in line:
                line = line.split('#')[0].strip()
            if line:
                results.append(self.parse_requirement(line))
        return results

    def resolve_with_pypi(self, package_name: str, version: str) -> List[ParsedRequirement]:
        deps = self.pypi_client.get_dependencies(package_name, version)
        parsed_deps = []
        for dep_str in deps:
            parsed_deps.append(self.parse_requirement(dep_str))
        return parsed_deps

def parse_requirements_line(req_line: str) -> Dict[str, Any]:
    if '#' in req_line:
        req_line = req_line.split('#')[0].strip()
    parser = RequirementParser()
    res = parser.parse_requirement(req_line)
    return {
        "name": res.name,
        "version": res.get("version"),
        "extras": res.extras,
        "environment_markers": res.environment_markers
    }
