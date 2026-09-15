import re
import io

try:
    from packaging.requirements import Requirement, InvalidRequirement
except ImportError:
    class InvalidRequirement(ValueError):
        """Raised when a requirement string is invalid."""
        pass

    class Requirement:
        """Fallback PEP 508 Requirement parser when packaging is not installed."""
        def __init__(self, requirement_string: str):
            req_str = requirement_string.strip()
            if not req_str:
                raise InvalidRequirement("Empty requirement string")

            # PEP 508 format structure:
            # name [extras] [specifiers] [; marker]

            # Separate environment marker if present (after ';')
            marker_str = None
            if ';' in req_str:
                parts = req_str.split(';', 1)
                req_str = parts[0].strip()
                marker_str = parts[1].strip()

            self.marker = marker_str if marker_str else None

            # Extract extras if present: name[extra1,extra2]
            extras_list = None
            if '[' in req_str and ']' in req_str:
                bracket_start = req_str.find('[')
                bracket_end = req_str.find(']')
                if bracket_end > bracket_start:
                    extras_raw = req_str[bracket_start + 1:bracket_end].strip()
                    if extras_raw:
                        extras_list = [e.strip() for e in extras_raw.split(',') if e.strip()]
                    else:
                        extras_list = []
                    req_str = req_str[:bracket_start].strip() + req_str[bracket_end + 1:].strip()

            self.extras = set(extras_list) if extras_list is not None else set()

            # Separate name and specifier
            # Valid package name per PEP 508: starts/ends with alphanumeric, can contain . _ -
            # Must be followed by whitespace, specifier operator, or end of string.
            name_match = re.match(r"^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)(.*)$", req_str)
            if not name_match:
                raise InvalidRequirement(f"Invalid package name in requirement: {requirement_string}")

            name = name_match.group(1)
            rest = name_match.group(2).strip()

            if rest:
                # Strip optional parentheses around specifier if present
                if rest.startswith('(') and rest.endswith(')'):
                    rest = rest[1:-1].strip()

                # Check that specifier begins with a valid PEP 508 specifier operator
                # PEP 508 valid operators: ===, ==, !=, <=, >=, ~=, <, >
                spec_match = re.match(r"^(===|==|!=|<=|>=|~=|<|>)\s*(.*)$", rest)
                if not spec_match:
                    raise InvalidRequirement(f"Invalid specifier in requirement: {requirement_string}")

                self.specifier = rest
            else:
                self.specifier = ""

            self.name = name

class RequirementParser:
    """Парсер требований PEP 508 для аудита безопасности."""

    def parse(self, req_line: str) -> dict:
        cleaned_line = req_line.strip()
        if not cleaned_line or cleaned_line.startswith("#"):
            raise ValueError("Empty or comment line")

        try:
            req = Requirement(cleaned_line)
        except InvalidRequirement as e:
            raise ValueError(f"Invalid requirement string: {req_line}") from e
        except Exception as e:
            raise ValueError(f"Invalid requirement string: {req_line}") from e

        operator = None
        version = None

        if req.specifier:
            spec_str = str(req.specifier)
            first_spec = spec_str.split(',')[0].strip()

            match = re.match(r"^([<>=!~]+)\s*(.*)$", first_spec)
            if match:
                operator = match.group(1)
                version = match.group(2)
            else:
                version = first_spec

        result = {
            "name": req.name,
            "operator": operator,
            "version": version,
        }

        if req.extras:
            result["extras"] = list(req.extras)

        if req.marker:
            result["marker"] = str(req.marker)

        return result

    def parse_stream(self, stream: io.BytesIO) -> list:
        content = stream.read().decode('utf-8')
        lines = content.splitlines()
        parsed_results = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                parsed = self.parse(line)
                parsed_results.append(parsed)
            except ValueError:
                continue

        return parsed_results

    def prepare_for_audit(self, parsed_req: dict) -> dict:
        name = parsed_req.get("name")
        operator = parsed_req.get("operator")
        version = parsed_req.get("version")

        constraint = f"{operator}{version}" if operator and version else (version or "")

        return {
            "package": name,
            "constraint": constraint
        }


def parse_requirement(req_line: str) -> dict:
    parser = RequirementParser()
    return parser.parse(req_line)
