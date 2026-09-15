import io
import re

try:
    from packaging.requirements import Requirement, InvalidRequirement
    HAS_PACKAGING = True
except ImportError:
    Requirement = None
    InvalidRequirement = None
    HAS_PACKAGING = False

from skills.pypi_client import PyPIClient

class PackageRequirementParser:
    def parse(self, requirement_str: str) -> dict:
        if not requirement_str or not isinstance(requirement_str, str):
            return {
                "name": "",
                "operator": None,
                "version": None,
                "extras": []
            }

        req_clean = requirement_str.strip()
        if not req_clean:
            return {
                "name": "",
                "operator": None,
                "version": None,
                "extras": []
            }

        if HAS_PACKAGING:
            try:
                req = Requirement(req_clean)
                name = req.name
                extras = list(req.extras)

                operator = None
                version = None

                if req.specifier:
                    specs = list(req.specifier)
                    if specs:
                        operator = specs[0].operator
                        version = specs[0].version

                return {
                    "name": name,
                    "operator": operator,
                    "version": version,
                    "extras": extras
                }
            except Exception:
                return {
                    "name": req_clean,
                    "operator": None,
                    "version": None,
                    "extras": []
                }

        return self._fallback_parse(req_clean)

    def _fallback_parse(self, req_clean: str) -> dict:
        # Separate environment marker if present (separated by ';')
        line_part = req_clean.split(';', 1)[0].strip()

        # Extract name, optional extras, and specifier portion
        # PEP 508 package names: letters, digits, '.', '-', '_'
        # Example: pkg-name[extra1,extra2] == 1.0.0, >= 2.0.0
        match = re.match(
            r'^(?P<name>[A-Za-z0-9_.\-]+)(?:\[(?P<extras>[^\]]*)\])?(?:\s*(?P<specifier>(?:~=|==|!=|<=|>=|<|>|===)\s*[\w\.\-\*\+]+.*))?$',
            line_part
        )

        if not match:
            return {
                "name": req_clean,
                "operator": None,
                "version": None,
                "extras": []
            }

        name = match.group("name")
        extras_raw = match.group("extras")
        extras = [e.strip() for e in extras_raw.split(',')] if extras_raw else []

        specifier_raw = match.group("specifier")
        operator = None
        version = None

        if specifier_raw:
            # Handle comma separated specifiers, e.g. "== 1.0.0, >= 2.0.0" or single "<= 1.0"
            first_spec = specifier_raw.split(',')[0].strip()
            spec_match = re.match(r'^(~=|==|!=|<=|>=|<|>|===)\s*([\w\.\-\*\+]+)', first_spec)
            if spec_match:
                operator = spec_match.group(1)
                version = spec_match.group(2)

        return {
            "name": name,
            "operator": operator,
            "version": version,
            "extras": extras
        }

    def parse_stream(self, stream):
        if hasattr(stream, 'read'):
            content = stream.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    yield self.parse(line)

def parse_requirement(requirement_str: str) -> dict:
    parser = PackageRequirementParser()
    return parser.parse(requirement_str)