import unittest
import uuid
import random
import sys
import os

from skills.cve_monitor import CVEMonitor
from skills.auto_patch_pipeline import AutoPatchPipeline, PipelineResult
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_validator import PatchValidator, ASTInspector, sandbox_exec


class TestCVEMonitorIntegration(unittest.TestCase):

    def setUp(self):
        self.cve_monitor = CVEMonitor()
        self.pipeline = AutoPatchPipeline()
        self.recovery_hub = ErrorRecoveryHub()
        self.validator = PatchValidator()
        self.random_suffix = uuid.uuid4().hex[:8]
        self.module_name = f"cve_monitor_test_mod_{self.random_suffix}"

    def test_cve_monitor_end_to_end_recovery_pipeline(self):
        random_error_message = f"CVE-2024-{random.randint(1000, 9999)} buffer overflow in {self.module_name}"
        test_exception = RuntimeError(random_error_message)
        test_traceback = f"Traceback (most recent call last):\n  File '{self.module_name}.py', line {random.randint(10, 100)}, in <module>\n    run_monitor()\n{type(test_exception).__name__}: {test_exception}"
        context = {"cve_id": f"CVE-2024-{random.randint(1000, 9999)}", "severity": "HIGH"}

        pipeline_result = self.pipeline.run_pipeline(
            module_name=self.module_name,
            exception=test_exception,
            traceback_str=test_traceback,
            context=context
        )

        self.assertIsInstance(pipeline_result, PipelineResult)
        self.assertTrue(hasattr(pipeline_result, "success"))
        self.assertTrue(hasattr(pipeline_result, "incident_id"))
        self.assertTrue(hasattr(pipeline_result, "patch_data"))

        incident_id = pipeline_result.incident_id
        if incident_id:
            logs = self.recovery_hub.get_incident_logs(incident_id)
            self.assertIsNotNone(logs)

        history = self.recovery_hub.get_incident_history(self.module_name)
        self.assertIsInstance(history, list)

        dummy_patch_code = f"def patched_func_{self.random_suffix}():\n    return 'secure_{self.random_suffix}'"
        validation_result = self.validator.verify_patch(dummy_patch_code)
        self.assertIsInstance(validation_result, dict)

        is_valid = self.validator.validate({"code": dummy_patch_code})
        self.assertIsInstance(is_valid, bool)

        stream_data = [dummy_patch_code]
        stream_verification = self.pipeline.verify_patch_stream(stream_data)
        self.assertIsNotNone(stream_verification)


if __name__ == "__main__":
    unittest.main()