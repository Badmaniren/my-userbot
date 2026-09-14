import unittest
import uuid
import random
import os
from skills.pypi_client import PyPIClient
from skills.auto_patch_pipeline import AutoPatchPipeline, PipelineResult
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_validator import PatchValidator

class IntegrationTestPyPIClientAndPipeline(unittest.TestCase):

    def setUp(self):
        self.pypi_client = PyPIClient()
        self.pipeline = AutoPatchPipeline()
        self.recovery_hub = ErrorRecoveryHub()
        self.validator = PatchValidator()
        self.random_package = f"test-pkg-{uuid.uuid4().hex[:8]}"
        self.random_incident_suffix = uuid.uuid4().hex[:6]

    def test_pypi_client_integration_with_pipeline_and_recovery(self):
        non_existent_version = f"{random.randint(10, 99)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        
        try:
            metadata = self.pypi_client.get_package_metadata(self.random_package)
            dependencies = self.pypi_client.get_package_dependencies(self.random_package, non_existent_version)
            self.fail("Expected exception due to non-existent package on PyPI")
        except Exception as e:
            tb_str = f"Traceback (most recent call last):\n  File 'test.py', line {random.randint(1, 100)}, in <module>\n    pypi_client.get_package_metadata('{self.random_package}')\n{type(e).__name__}: {str(e)}"
            context = {
                "run_id": uuid.uuid4().hex,
                "attempt": random.randint(1, 5),
                "target_module": "skills.pypi_client"
            }

            pipeline_result = self.pipeline.run_pipeline(
                module_name="skills.pypi_client",
                exception=e,
                traceback_str=tb_str,
                context=context
            )

            self.assertIsInstance(pipeline_result, PipelineResult)
            self.assertTrue(hasattr(pipeline_result, "success"))
            self.assertTrue(hasattr(pipeline_result, "incident_id"))
            self.assertTrue(hasattr(pipeline_result, "patch_data"))
            
            if pipeline_result.incident_id:
                logs = self.recovery_hub.get_incident_logs(pipeline_result.incident_id)
                self.assertIsNotNone(logs)

            history = self.recovery_hub.get_incident_history("skills.pypi_client")
            self.assertIsInstance(history, list)

            if pipeline_result.patch_data:
                is_valid = self.validator.validate(pipeline_result.patch_data)
                self.assertIsInstance(is_valid, bool)

    def test_force_analyze_and_recover_flow(self):
        dummy_exception = RuntimeError(f"PyPI API timeout error {uuid.uuid4().hex[:4]}")
        context = {
            "node_id": random.randint(1000, 9999),
            "env": "integration_test"
        }

        pipeline_result = self.pipeline.force_analyze_and_recover(
            module_name="skills.pypi_client",
            exception=dummy_exception,
            context=context
        )

        self.assertIsNotNone(pipeline_result)
        self.assertIsInstance(pipeline_result.success, bool)
        
        if pipeline_result.incident_id:
            incident_history = self.recovery_hub.get_incident_history("skills.pypi_client")
            self.assertTrue(any(pipeline_result.incident_id in str(item) for item in incident_history))

    def test_patch_validator_stream_verification(self):
        dummy_code = f"# -*- coding: utf-8 -*-\n# {uuid.uuid4().hex}\ndef dynamic_pypi_fix():\n    return True\n"
        validation_result = self.validator.verify_stream(dummy_code)
        self.assertIsInstance(validation_result, dict)

if __name__ == "__main__":
    unittest.main()