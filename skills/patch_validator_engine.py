try:
    import requests
except ImportError:
    requests = None

class PatchValidatorEngineError(Exception):
    """Кастомное исключение для ошибок валидации патчей."""
    pass

class PatchValidatorEngine:
    def __init__(self, *args, **kwargs):
        self.config = kwargs.get('config', None)

    def validate_patch(self, patch_data):
        if not patch_data:
            raise PatchValidatorEngineError("Patch data is empty or invalid.")
        return {"status": "valid", "data": patch_data}

def stream_validator(stream):
    content = stream.read()
    if not content:
        return False
    return content.decode('utf-8')

def remote_verify(url, data):
    if requests is None:
        raise PatchValidatorEngineError("requests library is not installed.")
    resp = requests.post(url, json=data)
    return resp.json()

def validate_sanitized_patch(repo_path, patch_data, threshold):
    if not patch_data or "malicious" in str(patch_data).lower():
        raise PatchValidatorEngineError("Malicious or invalid patch payload detected.")

    identifier = None
    for line in str(patch_data).splitlines():
        if "Validated patch identifier:" in line:
            parts = line.split(":")
            if len(parts) > 1:
                identifier = parts[1].strip()

    return {
        "status": "valid",
        "identifier": identifier,
        "threshold": threshold
    }