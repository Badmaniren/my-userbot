import unittest
import uuid
import random
import sys
import os

from skills.package_requirement_extractor import (
    extract_requirements,
    normalize_requirement
)
from pypi_client import PyPIClient
from error_recovery_hub import ErrorRecoveryHub
from patch_validator import PatchValidator, ASTInspector
from auto_patch_pipeline import AutoPatchPipeline, PipelineResult

class TestPackageRequirementExtractorIntegration(unittest.TestCase):

    def setUp(self):
        self.random_package_name = f"test-pkg-{uuid.uuid4().hex[:8]}"
        self.random_version = f"{random.randint(0, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.client = PyPIClient()
        self.hub = ErrorRecoveryHub()
        self.validator = PatchValidator()
        self.pipeline = AutoPatchPipeline()

    def test_end_to_end_requirement_extraction_and_error_handling(self):
        raw_dependency = f"requests (>={random.randint(1, 3)}.0.0); python_version < '3.10'"
        normalized = normalize_requirement(raw_dependency)
        
        self.assertIsInstance(normalized, str)
        self.assertTrue(len(normalized) > 0)

        fake_stream = f'{{"package": "{self.random_package_name}", "version": "{self.random_version}", "requires_dist": ["{raw_dependency}"]}}'
        stream_data = self.client.parse_stream_data(fake_stream)
        
        self.assertIsInstance(stream_data, dict)
        self.assertEqual(stream_data.get("package"), self.random_package_name)

        stream_verification = self.validator.verify_stream(fake_stream)
        self.assertIsInstance(stream_verification, dict)

        test_exception = ValueError(f"Failed to process requirement for {self.random_package_name}")
        traceback_str = "Traceback (most recent call last):\n  File 'test.py', line 1, in <module>\n    raise ValueError"
        context = {"session_id": uuid.uuid4().hex, "attempt": random.randint(1, 5)}

        pipeline_result = self.pipeline.run_pipeline(
            module_name=self.random_package_name,
            exception=test_exception,
            traceback_str=traceback_str,
            context=context
        )

        self.assertIsInstance(pipeline_result, PipelineResult)
        self.assertIsNotNone(pipeline_result.incident_id)

        incident_history = self.hub.get_incident_history(self.random_package_name)
        self.assertIsInstance(incident_history, list)

        incident_logs = self.hub.get_incident_logs(pipeline_result.incident_id)
        self.assertIsInstance(incident_logs, dict)

        safe_patch_code = f"def patched_extractor():\n    return '{uuid.uuid4().hex}'"
        static_analysis = self.validator.analyze_static(safe_patch_code)
        self.assertIsInstance(static_analysis, dict)

        is_valid_patch = self.validator.validate({"code": safe_patch_code})
        self.assertIsInstance(is_valid_patch, bool)

if __name__ == "__main__":
    unittest.main()