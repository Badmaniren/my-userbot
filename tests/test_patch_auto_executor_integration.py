import unittest
import uuid
import random
from skills.patch_auto_executor import execute_auto_patch_pipeline
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_scheduler import PatchScheduler

class TestPatchAutoExecutorIntegration(unittest.TestCase):
    def test_auto_patch_pipeline_integration(self):
        random_suffix = uuid.uuid4().hex[:8]
        module_name = f"test_module_{random_suffix}"
        error_message = f"Simulated failure {random_suffix}"
        exception = RuntimeError(error_message)
        traceback_str = f"Traceback (most recent call last):\n  File '{module_name}.py', line 10, in <module>\n    raise RuntimeError('{error_message}')"

        hub = ErrorRecoveryHub()
        scheduler = PatchScheduler()

        incident_id = hub.capture_failure(module_name, exception, traceback_str)
        self.assertIsNotNone(incident_id, "ErrorRecoveryHub must return an incident ID")

        analysis = hub.analyze_failure(incident_id)
        self.assertIsNotNone(analysis, "ErrorRecoveryHub must analyze the failure")

        patch_data = hub.generate_patch(incident_id)

        scheduled_task = scheduler.schedule_patch(module_name, exception, traceback_str)
        self.assertIsNotNone(scheduled_task, "PatchScheduler must schedule the patch")

        result = execute_auto_patch_pipeline(module_name=module_name, exception=exception, traceback_str=traceback_str)

        self.assertTrue(hasattr(result, "success"), "PipelineResult must have 'success' attribute")
        self.assertTrue(hasattr(result, "incident_id"), "PipelineResult must have 'incident_id' attribute")
        self.assertTrue(hasattr(result, "error"), "PipelineResult must have 'error' attribute")
        self.assertTrue(hasattr(result, "raw_result"), "PipelineResult must have 'raw_result' attribute")
        self.assertTrue(hasattr(result, "patch_data"), "PipelineResult must have 'patch_data' attribute")

        self.assertEqual(result.incident_id, incident_id, "PipelineResult incident_id must match the captured incident ID")

        history = hub.get_incident_history(module_name)
        self.assertIsInstance(history, list, "Incident history must be a list")
        self.assertGreater(len(history), 0, "Incident history must contain the recorded failure")

if __name__ == "__main__":
    unittest.main()