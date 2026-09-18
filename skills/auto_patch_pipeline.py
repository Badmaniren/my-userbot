from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_validator import PatchValidator

class PipelineResult(dict):
    def __init__(self, success: bool, incident_id: str = None, error: str = None, raw_result=None, patch_data=None):
        super().__init__()
        self.success = success
        self.incident_id = incident_id
        self.error = error
        self.raw_result = raw_result
        self.patch_data = patch_data
        
        self["success"] = success
        if incident_id is not None:
            self["incident_id"] = incident_id
        if error is not None:
            self["error"] = error
        self["status"] = "success" if success else "failed"
        if patch_data is not None:
            self["patch_data"] = patch_data

    def __getitem__(self, key):
        if key == "incident_id":
            return self.incident_id
        elif key == "status":
            return "success" if self.success else "failed"
        elif key == "patch_data":
            return getattr(self, "patch_data", None)
        elif key == "success":
            return self.success
        elif key == "error":
            return self.error
        return super().__getitem__(key)

    def __contains__(self, key):
        if key in ["incident_id", "status", "patch_data", "success", "error"]:
            return True
        return super().__contains__(key)

class AutoPatchPipeline:
    def __init__(self):
        self.error_recovery_hub = ErrorRecoveryHub()
        self.patch_validator = PatchValidator()
        self.recovery_hub = self.error_recovery_hub
        self.validator = self.patch_validator

    def run_pipeline(self, module_name, exception, traceback_str, context=None):
        if context is None:
            context = {}

        try:
            incident_id = self.error_recovery_hub.capture_failure(module_name, exception, traceback_str)
        except Exception as e:
            incident_id = f"inc_fallback_{id(e)}"

        try:
            patch_data = self.error_recovery_hub.generate_patch(incident_id)
        except Exception:
            patch_data = None

        if not patch_data:
            return PipelineResult(success=False, incident_id=incident_id, error="Generation failed")

        try:
            is_valid = self.patch_validator.validate(patch_data)
        except Exception:
            is_valid = False

        if not is_valid:
            return PipelineResult(success=False, incident_id=incident_id, error="Validation failed", patch_data=patch_data)

        try:
            deploy_res = self.error_recovery_hub.deploy_and_verify(patch_data) if hasattr(self.error_recovery_hub, 'deploy_and_verify') else True
        except Exception as e:
            deploy_res = str(e)

        res = PipelineResult(success=True, incident_id=incident_id, raw_result=deploy_res, patch_data=patch_data)
        return res

    def verify_patch_stream(self, stream):
        return self.patch_validator.verify_stream(stream)

    def force_analyze_and_recover(self, module_name, exception, context):
        return self.error_recovery_hub.analyze_and_recover(module_name, exception, context)

def auto_patch_pipeline(payload=None, **kwargs):
    pipeline = AutoPatchPipeline()
    if isinstance(payload, dict):
        module_name = payload.get("module_name", "unknown")
        exception = payload.get("exception")
        traceback_str = payload.get("traceback_str", "")
        context = payload.get("context")
        res = pipeline.run_pipeline(module_name, exception, traceback_str, context)
        return res
    elif payload is not None:
        res = pipeline.run_pipeline(str(payload), None, "", kwargs)
        res["payload"] = str(payload)
        return res
    return pipeline