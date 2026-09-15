import unittest
import io
import json
import uuid
import random
from skills.package_spec_parser import PackageSpecParser, PackageSpec, PyPIClient, AutoPatchPipeline, ErrorRecoveryHub, PatchValidator

class TestPackageSpecParserIntegration(unittest.TestCase):

    def setUp(self):
        self.parser = PackageSpecParser()
        self.pypi_client = PyPIClient()
        self.pipeline = AutoPatchPipeline()
        self.recovery_hub = ErrorRecoveryHub()
        self.validator = PatchValidator()
        self.random_seed = str(uuid.uuid4())[:8]

    def test_parse_single_spec_integration(self):
        pkg_name = f"requests-{self.random_seed}"
        version_num = f"{random.randint(1, 5)}.{random.randint(0, 9)}"
        spec_str = f"{pkg_name} (>={version_num},<3.0); python_version < '3.11'"
        
        spec = self.parser.parse(spec_str)
        
        self.assertIsInstance(spec, PackageSpec)
        self.assertEqual(spec.name, pkg_name)
        self.assertIn(version_num, spec.version)
        self.assertIsNotNone(spec.marker)

    def test_parse_stream_integration(self):
        pkgs = [
            f"numpy_{self.random_seed} (>=1.20)",
            f"pandas_{self.random_seed} [dev,test] ; extra == 'dev'",
            f"scipy_{self.random_seed} == 1.7.3"
        ]
        stream_data = "\n".join(pkgs).encode('utf-8')
        stream = io.BytesIO(stream_data)
        
        results = self.parser.parse_stream(stream)
        
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0].name, f"numpy_{self.random_seed}")
        self.assertEqual(results[1].extras, ["dev", "test"])
        self.assertEqual(results[2].version, "==1.7.3")

    def test_pypi_client_stream_data_integration(self):
        random_project = f"test-proj-{uuid.uuid4()}"
        payload = {"info": {"name": random_project, "version": "1.0.0"}, "urls": []}
        stream = io.BytesIO(json.dumps(payload).encode('utf-8'))
        
        data = self.pypi_client.parse_stream_data(stream)
        
        self.assertIsInstance(data, dict)
        self.assertEqual(data["info"]["name"], random_project)

    def test_pipeline_and_recovery_integration(self):
        mod_name = f"module_{uuid.uuid4().hex[:6]}"
        exc_msg = f"RuntimeError_{uuid.uuid4()}"
        
        result = self.pipeline.run_pipeline(
            module_name=mod_name,
            exception=Exception(exc_msg),
            traceback_str="Traceback (most recent call last):\n  File 'test.py', line 1",
            context={"seed": self.random_seed}
        )
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.incident_id)
        
        logs = self.recovery_hub.get_incident_logs(result.incident_id)
        self.assertIsInstance(logs, dict)
        
        history = self.recovery_hub.get_incident_history(mod_name)
        self.assertIsInstance(history, list)

    def test_patch_validator_integration(self):
        sample_code = f"x = {random.randint(100, 999)}\nprint(x)"
        validation_res = self.validator.verify_patch(sample_code)
        
        self.assertIsInstance(validation_res, dict)
        self.assertTrue(self.validator.validate("some patch data"))

if __name__ == '__main__':
    unittest.main()