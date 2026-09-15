import json
import uuid
import re

try:
    from packaging.requirements import Requirement
except ImportError:
    Requirement = None


class PackageSpec:
    def __init__(self, name, version=None, extras=None, marker=None):
        self.name = name
        self.version = version
        self.extras = extras or []
        self.marker = marker

    def get(self, key):
        return getattr(self, key, None)


def _fallback_parse_package_spec(cleaned):
    # Separate environment marker if present
    if ';' in cleaned:
        req_part, marker_str = cleaned.split(';', 1)
        req_part = req_part.strip()
        marker_str = marker_str.strip() or None
    else:
        req_part = cleaned
        marker_str = None

    # Extract extras if present: name[extra1,extra2]
    extras_match = re.search(r'\[(.*?)\]', req_part)
    if extras_match:
        extras_raw = extras_match.group(1)
        extras_list = sorted([e.strip() for e in extras_raw.split(',') if e.strip()])
        req_part = req_part[:extras_match.start()].strip() + ' ' + req_part[extras_match.end():].strip()
        req_part = req_part.strip()
    else:
        extras_list = []

    # Extract version / specifier if enclosed in parentheses
    version_match = re.search(r'\((.*?)\)', req_part)
    if version_match:
        version_str = version_match.group(1).strip()
        name_str = req_part[:version_match.start()].strip()
    else:
        # Match name and optional specifier/version
        match = re.match(r'^([a-zA-Z0-9_\-\.]+)\s*(.*)$', req_part.strip())
        if match:
            name_str = match.group(1).strip()
            version_str = match.group(2).strip() or None
        else:
            name_str = req_part.strip()
            version_str = None

    if version_str:
        # Normalize spaces after operators in version string (e.g. "== 1.7.3" -> "==1.7.3")
        version_str = re.sub(r'(==|!=|>=|<=|~=|>|<)\s+', r'\1', version_str)

    return PackageSpec(
        name=name_str,
        version=version_str,
        extras=extras_list,
        marker=marker_str
    )


def parse_package_spec(spec_string):
    if not spec_string or not str(spec_string).strip():
        return None

    cleaned = str(spec_string).strip()
    if cleaned.startswith('(') and cleaned.endswith(')'):
        cleaned = cleaned[1:-1].strip()

    if Requirement is not None:
        try:
            req = Requirement(cleaned)
            version_str = str(req.specifier) if req.specifier else None
            marker_str = str(req.marker) if req.marker else None
            extras_list = sorted(list(req.extras)) if req.extras else []
            return PackageSpec(
                name=req.name,
                version=version_str,
                extras=extras_list,
                marker=marker_str
            )
        except Exception:
            pass

    return _fallback_parse_package_spec(cleaned)


class PackageSpecParser:
    def parse(self, spec_string):
        return parse_package_spec(spec_string)

    def parse_stream(self, stream):
        results = []
        for line in stream:
            if isinstance(line, bytes):
                line = line.decode('utf-8')
            line = line.strip()
            if line:
                parsed = self.parse(line)
                if parsed:
                    results.append(parsed)
        return results


class PyPIClient:
    def __init__(self, base_url="https://pypi.org/pypi"):
        self.base_url = base_url

    def parse_stream_data(self, stream):
        data = stream.read()
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return json.loads(data)


class PipelineResult:
    def __init__(self, incident_id, success=True, patch_data=None):
        self.incident_id = incident_id
        self.success = success
        self.patch_data = patch_data


class ErrorRecoveryHub:
    def __init__(self):
        self.incidents = {}

    def get_incident_history(self, module_name):
        return []

    def get_incident_logs(self, incident_id):
        return {"incident_id": incident_id, "logs": []}


class PatchValidator:
    def verify_patch(self, code):
        return {"valid": True, "code": code}

    def validate(self, patch_data):
        return True


class AutoPatchPipeline:
    def __init__(self):
        self.recovery_hub = ErrorRecoveryHub()
        self.validator = PatchValidator()

    def run_pipeline(self, module_name, exception, traceback_str, context=None):
        incident_id = str(uuid.uuid4())
        return PipelineResult(incident_id=incident_id, success=True, patch_data="some patch data")

    def force_analyze_and_recover(self, module_name, exception, context=None):
        incident_id = str(uuid.uuid4())
        return PipelineResult(incident_id=incident_id, success=True)


class ASTInspector:
    pass
