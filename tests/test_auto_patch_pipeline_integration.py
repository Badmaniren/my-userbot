import unittest
import uuid
import random
from skills.auto_patch_pipeline import AutoPatchPipeline, PipelineResult

class TestAutoPatchPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.pipeline = AutoPatchPipeline()
        self.module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        self.exception_msg = f"RuntimeError_{random.randint(1000, 9999)}"
        self.traceback_str = f"Traceback (most recent call last):\n  File '{self.module_name}.py', line {random.randint(1, 100)}\n    raise {self.exception_msg}"

    def test_end_to_end_pipeline_flow(self):
        context = {"env": "integration_test", "run_id": str(uuid.uuid4())}
        
        result = self.pipeline.run_pipeline(
            module_name=self.module_name,
            exception=Exception(self.exception_msg),
            traceback_str=self.traceback_str,
            context=context
        )

        self.assertIsInstance(result, PipelineResult)
        self.assertIsNotNone(result.incident_id)
        self.assertTrue(len(result.incident_id) > 0)
        
        self.assertIn("success", result)
        self.assertIn("incident_id", result)
        self.assertIn("status", result)

    def test_force_analyze_and_recover_integration(self):
        context = {"force_recovery": True, "token": uuid.uuid4().hex}
        
        recovery_result = self.pipeline.force_analyze_and_recover(
            module_name=self.module_name,
            exception=Exception(self.exception_msg),
            context=context
        )

        self.assertIsNotNone(recovery_result)

if __name__ == "__main__":
    unittest.main()