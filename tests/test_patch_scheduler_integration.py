import unittest
import uuid
import random
import sys
import os

from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_scheduler import PatchScheduler
from skills.auto_patch_pipeline import PipelineResult

class TestPatchSchedulerIntegration(unittest.TestCase):
    def setUp(self):
        self.scheduler = PatchScheduler()
        self.recovery_hub = ErrorRecoveryHub()
        self.module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        self.random_error_msg = f"Randomized failure reason: {uuid.uuid4()}"
        self.exception = RuntimeError(self.random_error_msg)

    def test_end_to_end_patch_scheduling_and_application(self):
        incident_id = str(uuid.uuid4())
        random_code_snippet = f"def generated_fix_{uuid.uuid4().hex[:6]}(): return {random.randint(100, 999)}"
        
        patch_payload = {
            "incident_id": incident_id,
            "module_name": self.module_name,
            "patch_data": random_code_snippet,
            "success": True
        }

        captured_id = self.recovery_hub.capture_failure(
            module_name=self.module_name,
            exception=self.exception,
            traceback_str="Traceback (most recent call last):\n  File 'test.py', line 1, in <module>\n    raise self.exception"
        )
        
        self.assertIsNotNone(captured_id, "ErrorRecoveryHub must successfully capture the failure and return an incident ID.")

        scheduled_result = self.scheduler.coordinate_and_schedule(
            incident_id=incident_id,
            patch_payload=patch_payload,
            hub=self.recovery_hub
        )

        self.assertIsInstance(scheduled_result, PipelineResult, "Scheduler must return a PipelineResult instance.")
        self.assertTrue(scheduled_result.success, "Integration pipeline execution must report success.")
        self.assertEqual(scheduled_result.incident_id, incident_id, "Incident ID must match through the scheduling pipeline.")
        self.assertIn(random_code_snippet, str(scheduled_result.patch_data), "Patch data must be preserved and processed correctly.")

        history = self.recovery_hub.get_incident_history(self.module_name)
        self.assertIsInstance(history, list, "Incident history must be returned as a list.")
        self.assertTrue(any(incident_id in str(item) for item in history), "The processed incident must be present in the recovery hub history.")

if __name__ == "__main__":
    unittest.main()