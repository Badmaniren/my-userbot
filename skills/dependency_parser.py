import io
import re

try:
    from packaging.requirements import Requirement
    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False


def _normalize_requirement(req_str: str) -> dict:
    req_str = req_str.strip()
    if HAS_PACKAGING:
        req = Requirement(req_str)
        operator = None
        version = None
        if req.specifier:
            specs = list(req.specifier)
            if specs:
                operator = specs[0].operator
                version = specs[0].version

        markers = []
        env_marker_str = ""
        if req.marker:
            env_marker_str = str(req.marker)
            markers = [str(item) for item in req.marker._markers] if hasattr(req.marker, '_markers') else [env_marker_str]

        return {
            "name": req.name.lower(),
            "operator": operator,
            "version": version,
            "markers": markers,
            "environment_marker": env_marker_str
        }
    else:
        # Fallback regex parsing when packaging module is not installed
        # Separate main requirement from environment markers (after ';')
        parts = req_str.split(';', 1)
        main_part = parts[0].strip()
        env_marker_str = parts[1].strip() if len(parts) > 1 else ""

        # Extract package name and version specifier
        # Package names can contain letters, numbers, hyphens, underscores, dots
        pattern = r'^([A-Za-z0-9_.\-]+)\s*(?:([<>=!~^]+)\s*([A-Za-z0-9_.\-+*]+))?'
        match = re.match(pattern, main_part)

        if match:
            name = match.group(1).lower()
            operator = match.group(2) if match.group(2) else None
            version = match.group(3) if match.group(3) else None
        else:
            name = main_part.lower()
            operator = None
            version = None

        markers = [env_marker_str] if env_marker_str else []

        return {
            "name": name,
            "operator": operator,
            "version": version,
            "markers": markers,
            "environment_marker": env_marker_str
        }


def parse_requirement(req_string: str) -> dict:
    return _normalize_requirement(req_string)


def parse_requires_dist(req_string: str) -> dict:
    return _normalize_requirement(req_string)


class DependencyParser:
    def parse(self, req_string: str) -> dict:
        return parse_requirement(req_string)

    def parse_stream(self, stream: io.BytesIO) -> list:
        results = []
        content = stream.read().decode('utf-8')
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                results.append(parse_requirement(line))
        return results
