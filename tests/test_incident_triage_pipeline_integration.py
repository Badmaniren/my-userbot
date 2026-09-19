import unittest
import uuid
import random
import tempfile
import os
from skills.incident_triage_pipeline import triage_and_escalate_incident

class TestIncidentTriagePipelineIntegration(unittest.TestCase):
    def test_triage_and_escalate_flow(self):
        incident_id = f"inc-{uuid.uuid4()}"
        module_name = f"module_{random.randint(1000, 9999)}"
        error_messages = [
            "DatabaseConnectionError: Critical DB failure",
            "OutOfMemoryError: Container killed",
            "SegmentationFault: core dumped"
        ]
        exception_msg = random.choice(error_messages)
        traceback_str = f"Traceback (most recent call last):\n  File '{module_name}.py', line {random.randint(1, 100)}, in run\n    raise Exception('{exception_msg}')"
        
        with tempfile.TemporaryDirectory() as temp_dir:
            result = triage_and_escalate_incident(
                module_name=module_name,
                exception=Exception(exception_msg),
                traceback_str=traceback_str,
                incident_id=incident_id,
                workspace_dir=temp_dir
            )
            
            self.assertIsInstance(result, dict)
            self.assertIn("severity", result)
            self.assertIn("escalation_status", result)
            
            if result.get("severity") in ["HIGH", "CRITICAL", "SEV1", "SEV2"]:
                self.assertIn("escalation_result", result)

if __name__ == "__main__":
    unittest.main()