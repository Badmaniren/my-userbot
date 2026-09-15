import json
import requests
import io


class PyPIClient:
    def __init__(self, base_url="https://pypi.org/pypi"):
        self.base_url = base_url.rstrip("/")

    def get_package_metadata(self, pkg_name: str, version: str = None) -> dict:
        url = f"{self.base_url}/{pkg_name}/{version}/json" if version else f"{self.base_url}/{pkg_name}/json"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return {}

    def get_release_versions(self, pkg_name: str) -> list:
        url = f"{self.base_url}/{pkg_name}/json"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            releases = data.get("releases", {})
            return list(releases.keys())
        return []

    def get_dependencies(self, pkg_name: str, version: str = None) -> list:
        meta = self.get_package_metadata(pkg_name, version)
        return meta.get("info", {}).get("requires_dist", []) or []

    def get_package_dependencies(self, pkg_name: str, version: str = None) -> list:
        return self.get_dependencies(pkg_name, version)

    def parse_stream_data(self, stream) -> dict | None:
        if isinstance(stream, bytes):
            stream = io.BytesIO(stream)
        
        content = stream.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return None


class PipelineResult:
    def __init__(self, success: bool = True, incident_id: str = None):
        self.success = success
        self.incident_id = incident_id


class AutoPatchPipeline:
    def run_pipeline(self, module_name: str, exception: Exception, traceback_str: str, context: dict = None) -> PipelineResult:
        import uuid
        incident_id = str(uuid.uuid4())
        return PipelineResult(success=True, incident_id=incident_id)


class ErrorRecoveryHub:
    def get_incident_history(self, module_name: str) -> list:
        return []

    def get_incident_logs(self, incident_id: str) -> dict:
        return {"incident_id": incident_id, "logs": []}


class PatchValidator:
    def analyze_static(self, code: str) -> dict:
        return {"status": "valid"}

    def analyze_dynamic(self, code: str) -> dict:
        return {"status": "passed"}

    def validate(self, patch_data: dict) -> bool:
        return True