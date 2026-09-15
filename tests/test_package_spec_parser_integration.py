import unittest
import uuid
import random
from io import BytesIO
from skills.package_spec_parser import (
    PyPIClient,
    AutoPatchPipeline,
    ErrorRecoveryHub,
    PatchValidator,
    PipelineResult,
    ASTInspector
)

class TestPackageSpecParserIntegration(unittest.TestCase):
    def setUp(self):
        self.pypi_client = PyPIClient(base_url="https://pypi.org/pypi")
        self.recovery_hub = ErrorRecoveryHub()
        self.pipeline = AutoPatchPipeline()
        self.patch_validator = PatchValidator()
        self.module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        self.random_version = f"1.{random.randint(0, 9)}.{random.randint(0, 9)}"

    def test_integration_spec_parser_pipeline(self):
        raw_requires_dist = [
            f"requests (>=2.{random.randint(0, 9)}.0)",
            "pytest >= 6.0; python_version < '3.11'",
            "optional-dep[extra] ; extra == 'dev'"
        ]
        
        stream_data = f'{{"package": "{self.module_name}", "version": "{self.random_version}", "requires_dist": {str(raw_requires_dist)}}}'
        stream = BytesIO(stream_data.encode('utf-8'))

        parsed_stream = self.pypi_client.parse_stream_data(stream)
        self.assertIsNotNone(parsed_stream)
        self.assertEqual(parsed_stream.get("package"), self.module_name)

        exc = ValueError(f"Dependency resolution failed for {self.module_name}")
        traceback_str = f"Traceback (most recent call last):\n  File 'test.py', line {random.randint(1, 100)}, in <module>\n    raise ValueError"
        
        context = {
            "requires_dist": parsed_stream.get("requires_dist"),
            "random_token": uuid.uuid4().hex
        }

        pipeline_result = self.pipeline.run_pipeline(
            module_name=self.module_name,
            exception=exc,
            traceback_str=traceback_str,
            context=context
        )

        self.assertIsInstance(pipeline_result, PipelineResult)
        incident_id = pipeline_result.incident_id
        self.assertIsNotNone(incident_id)

        history = self.recovery_hub.get_incident_history(self.module_name)
        self.assertIsInstance(history, list)

        logs = self.recovery_hub.get_incident_logs(incident_id)
        self.assertIsInstance(logs, dict)

        random_code = f"import math\ndef dynamic_func_{random.randint(1000, 9999)}():\n    return math.sqrt({random.randint(1, 100)})"
        validation_res = self.patch_validator.verify_patch(random_code)
        self.assertIsInstance(validation_res, dict)

        if pipeline_result.patch_data:
            is_valid = self.patch_validator.validate(pipeline_result.patch_data)
            self.assertIsInstance(is_valid, bool)

    def test_force_analyze_and_recover_flow(self):
        test_exception = RuntimeError(f"Critical error {uuid.uuid4().hex}")
        forced_result = self.pipeline.force_analyze_and_recover(
            module_name=self.module_name,
            exception=test_exception,
            context={"attempt": random.randint(1, 50)}
        )
        self.assertIsInstance(forced_result, PipelineResult)
        self.assertTrue(hasattr(forced_result, "success"))
        self.assertTrue(hasattr(forced_result, "incident_id"))

if __name__ == "__main__":
    unittest.main()