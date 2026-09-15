import io
import re

try:
    from packaging.requirements import Requirement
    from packaging.markers import Marker
    from packaging.version import Version
    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False

class DependencyParserError(Exception):
    """Исключение при ошибке парсинга зависимостей."""
    pass

class Dependency:
    def __init__(self, name, version_constraint=None, marker=None, extras=None):
        self.name = name
        self.version_constraint = version_constraint
        self.marker = marker
        self.extras = extras or set()

def _parse_dependency_fallback(req_str: str) -> Dependency:
    if not req_str or not isinstance(req_str, str) or not req_str.strip():
        raise DependencyParserError("Empty or invalid dependency string")

    s = req_str.strip()

    # Extract marker
    marker = None
    if ';' in s:
        s, marker_part = s.split(';', 1)
        marker = marker_part.strip() or None
        s = s.strip()

    # Extract extras
    extras = set()
    extras_match = re.search(r'\[(.*?)\]', s)
    if extras_match:
        raw_extras = extras_match.group(1)
        extras = {e.strip() for e in raw_extras.split(',') if e.strip()}
        s = (s[:extras_match.start()] + s[extras_match.end():]).strip()

    # Extract name and version constraint
    name_match = re.match(r'^([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)(.*)$', s)
    if not name_match:
        raise DependencyParserError(f"Invalid dependency string: {req_str}")

    name = name_match.group(1)
    rest = name_match.group(2).strip()

    # Remove surrounding parentheses from rest if present
    if rest.startswith('(') and rest.endswith(')'):
        rest = rest[1:-1].strip()

    version_constraint = None
    if rest:
        spec_pattern = r'^\s*(?:(?:==|!=|<=|>=|<|>|~=|===)\s*[\w.*+-]+)(?:\s*,\s*(?:==|!=|<=|>=|<|>|~=|===)\s*[\w.*+-]+)*\s*$'
        if not re.match(spec_pattern, rest):
            raise DependencyParserError(f"Invalid version constraint in: {req_str}")
        version_constraint = rest

    return Dependency(
        name=name,
        version_constraint=version_constraint,
        marker=marker,
        extras=extras
    )

def parse_dependency(req_str: str) -> Dependency:
    if not req_str or not isinstance(req_str, str) or not req_str.strip():
        raise DependencyParserError("Empty or invalid dependency string")

    if HAS_PACKAGING:
        try:
            req = Requirement(req_str)
        except Exception as e:
            raise DependencyParserError(f"Invalid dependency string: {req_str}") from e

        version_constraint = str(req.specifier) if req.specifier else None
        marker = str(req.marker) if req.marker else None

        return Dependency(
            name=req.name,
            version_constraint=version_constraint,
            marker=marker,
            extras=req.extras
        )
    else:
        return _parse_dependency_fallback(req_str)

def parse_stream_data(stream):
    if isinstance(stream, io.IOBase):
        content = stream.read()
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        lines = content.splitlines()
    elif isinstance(stream, dict):
        requires = stream.get("requires_dist", [])
        results = []
        for r in requires:
            try:
                dep = parse_dependency(r)
                results.append({
                    "name": dep.name,
                    "version": dep.version_constraint,
                    "marker": str(dep.marker) if dep.marker else None
                })
            except DependencyParserError:
                continue
        return results
    else:
        lines = [str(stream)]

    results = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            dep = parse_dependency(line)
            results.append({
                "name": dep.name,
                "version": dep.version_constraint,
                "marker": str(dep.marker) if dep.marker else None
            })
        except DependencyParserError:
            continue
    return results

class PyPIClient:
    def parse_stream_data(self, stream_data):
        if isinstance(stream_data, dict):
            requires = stream_data.get("requires_dist", [])
            parsed = []
            for req in requires:
                try:
                    dep = parse_dependency(req)
                    parsed.append({
                        "name": dep.name,
                        "version": dep.version_constraint,
                        "marker": str(dep.marker) if dep.marker else None
                    })
                except DependencyParserError:
                    pass
            return parsed
        return []

class PipelineResult:
    def __init__(self, incident_id, success=True):
        self.incident_id = incident_id
        self.success = success

class ErrorRecoveryHub:
    def __init__(self):
        self.history = {}
        self.logs = {}

    def get_incident_history(self, module_name: str):
        return self.history.get(module_name, [])

    def get_incident_logs(self, incident_id: str):
        return self.logs.get(incident_id, {"status": "logged"})

class PatchValidator:
    def verify_stream(self, stream_data: dict) -> dict:
        return {"status": "verified", "package": stream_data.get("package")}

    def validate(self, patch_dict: dict) -> bool:
        return isinstance(patch_dict, dict) and "code" in patch_dict

class AutoPatchPipeline:
    def __init__(self):
        self.recovery_hub = ErrorRecoveryHub()
        self.validator = PatchValidator()

    def run_pipeline(self, module_name: str, exception: Exception, traceback_str: str, context: dict = None) -> PipelineResult:
        import uuid
        incident_id = str(uuid.uuid4())
        self.recovery_hub.history.setdefault(module_name, []).append(incident_id)
        self.recovery_hub.logs[incident_id] = {
            "module": module_name,
            "exception": str(exception),
            "traceback": traceback_str,
            "context": context
        }
        return PipelineResult(incident_id=incident_id, success=True)

    def force_analyze_and_recover(self, module_name: str, exception: Exception, context: dict = None) -> PipelineResult:
        import uuid
        incident_id = str(uuid.uuid4())
        self.recovery_hub.history.setdefault(module_name, []).append(incident_id)
        self.recovery_hub.logs[incident_id] = {
            "module": module_name,
            "exception": str(exception),
            "context": context
        }
        return PipelineResult(incident_id=incident_id, success=True)
