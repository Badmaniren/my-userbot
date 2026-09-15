import unittest
import uuid
import random
import io
import json
from skills.package_requirement_parser import PyPIClient
from skills.auto_patch_pipeline import AutoPatchPipeline, PipelineResult
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_validator import PatchValidator, ASTInspector

class TestPackageRequirementParserIntegration(unittest.TestCase):

    def setUp(self):
        self.pypi_client = PyPIClient()
        self.auto_patch_pipeline = AutoPatchPipeline()
        self.error_recovery_hub = ErrorRecoveryHub()
        self.patch_validator = PatchValidator()

        self.random_package = f"test-pkg-{uuid.uuid4().hex[:8]}"
        self.random_version = f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.random_module = f"module_{uuid.uuid4().hex[:6]}"
        self.random_error_msg = f"DependencyResolutionError_{uuid.uuid4().hex[:6]}"

    def test_dependency_chain_and_recovery_pipeline(self):
        stream_data = {
            "package": self.random_package,
            "version": self.random_version,
            "requires_dist": [f"dep-{uuid.uuid4().hex[:4]} (>=1.0.0)", f"dep-{uuid.uuid4().hex[:4]} (<2.0)"]
        }
        json_bytes = json.dumps(stream_data).encode("utf-8")
        stream = io.BytesIO(json_bytes)

        parsed_stream = self.pypi_client.parse_stream_data(stream)
        self.assertIsNotNone(parsed_stream)
        self.assertEqual(parsed_stream.get("package"), self.random_package)

        stream_validation = self.patch_validator.verify_stream(stream)
        self.assertIsInstance(stream_validation, dict)

        exc = ImportError(self.random_error_msg)
        tb_str = f"Traceback (most recent call last):\n  File '<string>', line 1, in <module>\nImportError: {self.random_error_msg}"
        context = {"dependency_stream": parsed_stream, "run_id": uuid.uuid4().hex}

        pipeline_result = self.auto_patch_pipeline.run_pipeline(
            module_name=self.random_module,
            exception=exc,
            traceback_str=tb_str,
            context=context
        )

        self.assertIsInstance(pipeline_result, PipelineResult)
        self.assertIsNotNone(pipeline_result.incident_id)

        history = self.error_recovery_hub.get_incident_history(self.random_module)
        self.assertIsInstance(history, list)

        logs = self.error_recovery_hub.get_incident_logs(pipeline_result.incident_id)
        self.assertIsInstance(logs, dict)

        if pipeline_result.patch_data:
            is_valid = self.patch_validator.validate(pipeline_result.patch_data)
            self.assertIsInstance(is_valid, bool)

    def test_force_analyze_and_recover_flow(self):
        exc = RuntimeError(self.random_error_msg)
        context = {"retry_count": random.randint(1, 5), "token": uuid.uuid4().hex}

        result = self.auto_patch_pipeline.force_analyze_and_recover(
            module_name=self.random_module,
            exception=exc,
            context=context
        )

        self.assertIsInstance(result, PipelineResult)

        if result.success and result.patch_data:
            validation_result = self.patch_validator.validate(result.patch_data)
            self.assertTrue(validation_result)

if __name__ == "__main__":
    unittest.main()