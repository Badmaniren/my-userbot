from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_validator import PatchValidator

class PipelineResult:
    def __init__(self, success: bool, incident_id: str = None, error: str = None, raw_result=None):
        self.success = success
        self.incident_id = incident_id
        self.error = error
        self.raw_result = raw_result

    def __getitem__(self, key):
        if key == "incident_id":
            return self.incident_id
        elif key == "status":
            return "success" if self.success else "failed"
        elif key == "patch_data":
            return getattr(self, "patch_data", None)
        raise KeyError(key)

    def __contains__(self, key):
        return key in ["incident_id", "status", "patch_data"]

class AutoPatchPipeline:
    def __init__(self):
        self.error_recovery_hub = ErrorRecoveryHub()
        self.patch_validator = PatchValidator()
        self.recovery_hub = self.error_recovery_hub
        self.validator = self.patch_validator

    def run_pipeline(self, module_name, exception, traceback_str, context=None):
        if context is None:
            context = {}

        incident_id = self.error_recovery_hub.capture_failure(module_name, exception, traceback_str)
        
        patch_data = self.error_recovery_hub.generate_patch(incident_id)
        if not patch_data:
            return PipelineResult(success=False, incident_id=incident_id, error="Generation failed")

        is_valid = self.patch_validator.validate(patch_data)
        if not is_valid:
            return PipelineResult(success=False, incident_id=incident_id, error="Validation failed")

        deploy_res = self.error_recovery_hub.deploy_and_verify(patch_data) if hasattr(self.error_recovery_hub, 'deploy_and_verify') else True

        res = PipelineResult(success=True, incident_id=incident_id, raw_result=deploy_res)
        res.patch_data = patch_data
        return res

    def verify_patch_stream(self, stream):
        return self.patch_validator.verify_stream(stream)

    def force_analyze_and_recover(self, module_name, exception, context):
        return self.error_recovery_hub.analyze_and_recover(module_name, exception, context)