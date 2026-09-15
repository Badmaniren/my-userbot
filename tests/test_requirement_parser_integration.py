import unittest
import uuid
import random
from skills.requirement_parser import parse_requirement
from skills.pypi_client import PyPIClient
from skills.patch_validator import PatchValidator
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.auto_patch_pipeline import AutoPatchPipeline

class TestRequirementParserIntegration(unittest.TestCase):
    def setUp(self):
        self.pypi_client = PyPIClient()
        self.patch_validator = PatchValidator()
        self.error_recovery_hub = ErrorRecoveryHub()
        self.auto_patch_pipeline = AutoPatchPipeline()

    def test_requirement_parser_integration_flow(self):
        rand_id = str(uuid.uuid4())
        packages = ["requests", "flask", "numpy", "django", "pytest"]
        versions = [">=2.0.0", "==1.19.2", "<3.0,>=1.0.0", "!=1.4.0"]

        selected_pkg = random.choice(packages)
        selected_ver = random.choice(versions)
        raw_requirement = f"{selected_pkg} ({selected_ver})"

        parsed_name, parsed_constraints = parse_requirement(raw_requirement)

        self.assertEqual(parsed_name, selected_pkg)
        formatted_constraints = ",".join(f"{op}{v}" for op, v in parsed_constraints)
        self.assertEqual(formatted_constraints, selected_ver.strip("()"))

        try:
            metadata = self.pypi_client.get_package_metadata(parsed_name, None)
            self.assertIsInstance(metadata, dict)
        except Exception as e:
            trace_str = f"Error during pypi fetch for {rand_id}"
            incident = self.error_recovery_hub.capture_failure(
                module_name="skills.requirement_parser",
                exception=e,
                traceback_str=trace_str
            )
            self.assertIsNotNone(incident)

            history = self.error_recovery_hub.get_incident_history("skills.requirement_parser")
            self.assertIsInstance(history, list)

            pipeline_res = self.auto_patch_pipeline.run_pipeline(
                module_name="skills.requirement_parser",
                exception=e,
                traceback_str=trace_str,
                context={"uuid": rand_id}
            )
            self.assertIsInstance(pipeline_res.success, bool)

if __name__ == "__main__":
    unittest.main()