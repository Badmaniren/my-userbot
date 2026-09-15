import re
import requests

try:
    from packaging.requirements import Requirement
    from packaging.markers import Marker
    HAS_PACKAGING = True
except ImportError:
    Requirement = None
    Marker = None
    HAS_PACKAGING = False


def _fallback_parse(req_string: str) -> dict:
    s = req_string.strip()
    if not s:
        return {'name': '', 'constraints': None, 'version_constraint': None, 'extras': [], 'marker': None}

    marker = None
    if ';' in s:
        req_part, marker_part = s.split(';', 1)
        req_part = req_part.strip()
        marker = marker_part.strip() or None
    else:
        req_part = s

    pattern = r'^([a-zA-Z0-9_\-\.]+)(?:\[(.*?)\])?\s*(.*)$'
    match = re.match(pattern, req_part)

    if not match:
        first_token = req_part.split()[0] if req_part else s.split()[0]
        return {
            'name': first_token,
            'constraints': None,
            'version_constraint': None,
            'extras': [],
            'marker': marker
        }

    name = match.group(1)
    extras_str = match.group(2)
    rest = match.group(3).strip()

    extras = []
    if extras_str:
        extras = [e.strip() for e in extras_str.split(',') if e.strip()]

    constraints = None
    if rest:
        rest_clean = rest.strip()
        if rest_clean.startswith('(') and rest_clean.endswith(')'):
            rest_clean = rest_clean[1:-1].strip()
        if rest_clean:
            if re.match(r'^(~=|==|!=|<=|>=|===|<|>|@)', rest_clean):
                constraints = rest_clean
            else:
                first_token = s.split()[0]
                return {
                    'name': first_token,
                    'constraints': None,
                    'version_constraint': None,
                    'extras': [],
                    'marker': None
                }

    return {
        'name': name,
        'constraints': constraints,
        'version_constraint': constraints,
        'extras': extras,
        'marker': marker
    }


class DependencyParser:
    def parse(self, req_string: str) -> dict:
        if HAS_PACKAGING:
            try:
                req = Requirement(req_string)
                extras = list(req.extras) if req.extras else []
                marker = str(req.marker) if req.marker else None
                specifier = str(req.specifier) if req.specifier else None

                return {
                    'name': req.name,
                    'constraints': specifier,
                    'version_constraint': specifier,
                    'extras': extras,
                    'marker': marker
                }
            except Exception:
                return _fallback_parse(req_string)
        else:
            return _fallback_parse(req_string)

    def parse_stream(self, stream) -> list:
        dependencies = []
        for line in stream:
            decoded = line.decode('utf-8').strip()
            if decoded and not decoded.startswith('#'):
                dependencies.append(self.parse(decoded))
        return dependencies

    def fetch_and_parse(self, url: str) -> list:
        response = requests.get(url)
        data = response.json()
        requires_dist = data.get("info", {}).get("requires_dist", [])
        return [self.parse(req) for req in requires_dist]


def parse_dependency(req_string: str) -> dict:
    return DependencyParser().parse(req_string)


def parse_dependency_string(req_string: str) -> dict:
    return DependencyParser().parse(req_string)
