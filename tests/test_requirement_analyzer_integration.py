import unittest
import uuid
import random
import sys
import os

from skills.requirement_analyzer import RequirementAnalyzer
from skills.pypi_client import PyPIClient
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.patch_validator import PatchValidator
from skills.auto_patch_pipeline import AutoPatchPipeline

class TestRequirementAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.analyzer = RequirementAnalyzer()
        self.pypi_client = PyPIClient()
        self.recovery_hub = ErrorRecoveryHub()
        self.patch_validator = PatchValidator()
        self.pipeline = AutoPatchPipeline()
        
        self.rand_str = str(uuid.uuid4())
        self.package_name = f"test-pkg-{self.rand_str[:8]}"
        self.random_version = f"1.{random.randint(0, 9)}.{random.randint(0, 9)}"

    def test_pep508_specifier_parsing_with_pypi_integration(self):
        specifier_string = f"{self.package_name} >={self.random_version}"
        
        parsed_requirements = self.analyzer.parse(specifier_string)
        
        self.assertIsInstance(parsed_requirements, list)
        self.assertTrue(len(parsed_requirements) > 0)
        
        req = parsed_requirements[0]
        self.assertEqual(req.get("name"), self.package_name)
        
        versions = self.pypi_client.get_release_versions(req.get("name"))
        self.assertIsInstance(versions, list)

    def test_pipeline_and_error_recovery_flow(self):
        module_name = f"mod_{self.rand_str[:6]}"
        exception_msg = f"SecurityAuditFailure-{random.randint(1000, 9999)}"
        exc = RuntimeError(exception_msg)
        
        result = self.pipeline.run_pipeline(
            module_name=module_name,
            exception=exc,
            traceback_str="Traceback (most recent call last):\n  File 'test.py', line 1, in <module>\n    raise RuntimeError()",
            context={"audit_id": self.rand_str}
        )
        
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "success"))
        
        history = self.recovery_hub.get_incident_history(module_name)
        self.assertIsInstance(history, list)

    def test_patch_validation_stream_processing(self):
        dummy_code = f"x = {random.randint(1, 100)}\nprint(x)"
        validation_result = self.patch_validator.verify_patch(dummy_code)
        
        self.assertIsInstance(validation_result, dict)

if __name__ == "__main__":
    unittest.main()