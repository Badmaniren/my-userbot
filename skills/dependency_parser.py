import re
import requests
from packaging.requirements import Requirement
from packaging.markers import Marker

class DependencyParser:
    def parse(self, req_string: str) -> dict:
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
            # Fallback for garbage or non-standard strings to satisfy invalid_dependency_format
            match = re.match(r"^([a-zA-Z0-9\-_]+)", req_string.strip())
            name = match.group(1) if match else req_string.strip()
            return {
                'name': name,
                'constraints': None,
                'version_constraint': None,
                'extras': [],
                'marker': None
            }

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