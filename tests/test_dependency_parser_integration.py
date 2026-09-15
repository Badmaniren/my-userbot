import unittest
import uuid
import random
import io
from skills.dependency_parser import (
    parse_dependency,
    parse_stream_data,
    Dependency,
    DependencyParserError,
    PyPIClient,
    AutoPatchPipeline,
    ErrorRecoveryHub,
    PatchValidator,
    PipelineResult
)

class TestDependencyParserIntegration(unittest.TestCase):

    def setUp(self):
        self.pipeline = AutoPatchPipeline()
        self.pypi_client = PyPIClient()
        self.validator = PatchValidator()
        self.random_pkg_id = f"secure-pkg-{uuid.uuid4().hex[:8]}"
        self.random_version = f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}"

    def test_end_to_end_dependency_parsing_pipeline(self):
        test_deps = [
            f"requests (>=2.25.0,<3.0.0); python_version < '{random.randint(3, 9)}'",
            f"urllib3 >= 1.26.0 ; extra == 'security'",
            "invalid_dependency_string_!@#$"
        ]

        stream_payload = {
            "package": self.random_pkg_id,
            "version": self.random_version,
            "requires_dist": test_deps
        }

        parsed_via_pypi = self.pypi_client.parse_stream_data(stream_payload)
        self.assertIsInstance(parsed_via_pypi, list)

        stream_io = io.BytesIO("\n".join(test_deps).encode("utf-8"))
        parsed_via_stream = parse_stream_data(stream_io)
        self.assertIsInstance(parsed_via_stream, list)

        valid_count = 0
        for dep_str in test_deps[:2]:
            try:
                dep_obj = parse_dependency(dep_str)
                self.assertIsInstance(dep_obj, Dependency)
                self.assertTrue(len(dep_obj.name) > 0)
                valid_count += 1
            except DependencyParserError:
                pass

        self.assertGreaterEqual(valid_count, 1)

        try:
            parse_dependency(test_deps[2])
            self.fail("Expected DependencyParserError for invalid dependency")
        except DependencyParserError as e:
            trace_str = f"Traceback (most recent call last):\n  File 'test.py', line 10, in <module>\n    parse_dependency('{test_deps[2]}')\nDependencyParserError: {e}"

            pipeline_result = self.pipeline.run_pipeline(
                module_name="skills.dependency_parser",
                exception=e,
                traceback_str=trace_str,
                context={"package": self.random_pkg_id, "invalid_str": test_deps[2]}
            )

            self.assertIsInstance(pipeline_result, PipelineResult)
            self.assertTrue(pipeline_result.success)
            self.assertIsNotNone(pipeline_result.incident_id)

            history = self.pipeline.recovery_hub.get_incident_history("skills.dependency_parser")
            self.assertIn(pipeline_result.incident_id, history)

            logs = self.pipeline.recovery_hub.get_incident_logs(pipeline_result.incident_id)
            self.assertEqual(logs["module"], "skills.dependency_parser")
            self.assertIn(self.random_pkg_id, str(logs["context"]))

            verified_stream = self.validator.verify_stream(stream_payload)
            self.assertEqual(verified_stream.get("status"), "verified")
            self.assertEqual(verified_stream.get("package"), self.random_pkg_id)

            patch_data = {"code": f"def fix_{uuid.uuid4().hex[:6]}(): pass", "package": self.random_pkg_id}
            is_valid_patch = self.validator.validate(patch_data)
            self.assertTrue(is_valid_patch)

    def test_force_analyze_and_recover_flow(self):
        custom_exception = ValueError(f"Random security failure {uuid.uuid4().hex}")
        forced_result = self.pipeline.force_analyze_and_recover(
            module_name="skills.dependency_parser",
            exception=custom_exception,
            context={"hazard_id": random.randint(1000, 9999)}
        )

        self.assertIsInstance(forced_result, PipelineResult)
        self.assertTrue(forced_result.success)

        history = self.pipeline.recovery_hub.get_incident_history("skills.dependency_parser")
        self.assertIn(forced_result.incident_id, history)

        incident_logs = self.pipeline.recovery_hub.get_incident_logs(forced_result.incident_id)
        self.assertEqual(incident_logs["module"], "skills.dependency_parser")
        self.assertIn(str(custom_exception), incident_logs["exception"])

if __name__ == "__main__":
    unittest.main()