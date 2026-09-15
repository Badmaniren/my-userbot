import unittest
import uuid
import random
from skills.package_requirement_reader import (
    PyPIClient,
    AutoPatchPipeline,
    ErrorRecoveryHub,
    PatchValidator
)

class TestPackageRequirementReaderIntegration(unittest.TestCase):

    def setUp(self):
        self.pypi_client = PyPIClient()
        self.auto_patch_pipeline = AutoPatchPipeline()
        self.error_recovery_hub = ErrorRecoveryHub()
        self.patch_validator = PatchValidator()
        
        self.test_package = f"test-pkg-{uuid.uuid4().hex[:8]}"
        self.test_version = f"1.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.random_incident_id = str(uuid.uuid4())

    def test_pypi_metadata_and_dependencies_integration(self):
        versions = self.pypi_client.get_release_versions(self.test_package)
        self.assertIsInstance(versions, list)

        metadata = self.pypi_client.get_package_metadata(self.test_package, self.test_version)
        self.assertIsInstance(metadata, dict)

        deps = self.pypi_client.get_dependencies(self.test_package, self.test_version)
        self.assertIsInstance(deps, list)

        pkg_deps = self.pypi_client.get_package_dependencies(self.test_package, self.test_version)
        self.assertIsInstance(pkg_deps, list)

    def test_pipeline_and_recovery_hub_integration(self):
        module_name = f"mod_{uuid.uuid4().hex[:6]}"
        exception_msg = f"Error-{random.randint(1000, 9999)}"
        exception_obj = RuntimeError(exception_msg)
        traceback_str = "Traceback (most recent call last):\n  File 'test.py', line 1, in <module>\n    raise RuntimeError()"
        context = {"random_seed": random.randint(1, 100)}

        pipeline_result = self.auto_patch_pipeline.run_pipeline(
            module_name=module_name,
            exception=exception_obj,
            traceback_str=traceback_str,
            context=context
        )

        self.assertIsNotNone(pipeline_result)
        self.assertTrue(hasattr(pipeline_result, "success"))
        self.assertTrue(hasattr(pipeline_result, "incident_id"))

        history = self.error_recovery_hub.get_incident_history(module_name)
        self.assertIsInstance(history, list)

        if pipeline_result.incident_id:
            logs = self.error_recovery_hub.get_incident_logs(pipeline_result.incident_id)
            self.assertIsInstance(logs, dict)

    def test_patch_validator_and_stream_parsing(self):
        dummy_code = f"def generated_func_{random.randint(1, 1000)}():\n    return {random.randint(10, 99)}"
        
        static_analysis = self.patch_validator.analyze_static(dummy_code)
        self.assertIsInstance(static_analysis, dict)

        dynamic_analysis = self.patch_validator.analyze_dynamic(dummy_code)
        self.assertIsInstance(dynamic_analysis, dict)

        validation_result = self.patch_validator.validate({"code": dummy_code, "id": self.random_incident_id})
        self.assertIsInstance(validation_result, bool)

        stream_data = f'{{"package": "{self.test_package}", "version": "{self.test_version}"}}'.encode('utf-8')
        parsed_stream = self.pypi_client.parse_stream_data(stream_data)
        
        if parsed_stream is not None:
            self.assertIsInstance(parsed_stream, dict)

if __name__ == "__main__":
    unittest.main()