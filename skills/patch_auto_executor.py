from skills.auto_patch_pipeline import AutoPatchPipeline
from skills.error_recovery_hub import ErrorRecoveryHub


class ExecutionResult:
    def __init__(self, success: bool, incident_id: str, patch_data: dict, error=None):
        self.success = success
        self.incident_id = incident_id
        self.patch_data = patch_data
        self.error = error


class PatchAutoExecutor:
    def __init__(self):
        self.pipeline = AutoPatchPipeline()
        self.hub = ErrorRecoveryHub()

    def execute_auto_patch(self, module_name, exception, traceback_str, context=None):
        try:
            return self.pipeline.run_pipeline(module_name, exception, traceback_str, context)
        except Exception:
            fallback = self.hub.analyze_and_recover(module_name, exception, context)
            return fallback

    def verify_stream(self, stream_data):
        return self.pipeline.verify_patch_stream(stream_data)

    def force_recovery(self, module_name, exception, context=None):
        return self.pipeline.force_analyze_and_recover(module_name, exception, context)

    def capture_incident(self, module_name, exception, traceback_str):
        return self.hub.capture_failure(module_name, exception, traceback_str)

    def deploy_patch_payload(self, incident_id, patch_data):
        return self.hub.deploy_and_verify(incident_id, patch_data)

    def execute_and_patch(self, module_name, exception, traceback_str, context=None):
        return self.execute_auto_patch(module_name, exception, traceback_str, context)

    def verify_and_execute_stream(self, stream_data):
        return self.verify_stream(stream_data)