import unittest
import uuid
import random
import io
from skills.cve_fetcher import (
    AutoPatchPipeline,
    ErrorRecoveryHub,
    PatchValidator,
    ASTInspector,
    PipelineResult,
    sandbox_exec,
    fetch_cve_feeds
)

class TestCVEFetcherIntegration(unittest.TestCase):

    def setUp(self):
        self.hub = ErrorRecoveryHub()
        self.validator = PatchValidator()
        self.pipeline = AutoPatchPipeline(hub=self.hub, validator=self.validator)
        self.random_module_name = f"cve_module_{uuid.uuid4().hex[:8]}"
        self.random_error_msg = f"Connection timeout error: {uuid.uuid4().hex}"
        self.test_exception = ConnectionError(self.random_error_msg)
        self.random_context = {"url": f"https://cve.mitre.org/api/v4/{uuid.uuid4().hex}", "retry_count": random.randint(1, 5)}

    def test_end_to_end_error_recovery_and_pipeline(self):
        traceback_str = f"Traceback (most recent call last):\n  File 'cve_fetcher.py', line {random.randint(10, 100)}, in fetch\n{self.random_error_msg}"

        result = self.pipeline.run_pipeline(
            module_name=self.random_module_name,
            exception=self.test_exception,
            traceback_str=traceback_str,
            context=self.random_context
        )

        self.assertIsInstance(result, PipelineResult)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.incident_id)
        self.assertIsNone(result.error)
        self.assertIsInstance(result.patch_data, dict)

        incident_logs = self.hub.get_incident_logs(result.incident_id)
        self.assertIsInstance(incident_logs, dict)
        self.assertEqual(incident_logs.get("module_name"), self.random_module_name)
        self.assertEqual(incident_logs.get("exception"), self.random_error_msg)

        history = self.hub.get_incident_history(self.random_module_name)
        self.assertIsInstance(history, list)
        self.assertTrue(any(inc["incident_id"] == result.incident_id for inc in history))

    def test_patch_validator_and_stream_integration(self):
        sample_code = f"x = {random.randint(1, 100)}\ny = {random.randint(101, 200)}\nresult_sum = x + y"

        static_res = self.validator.analyze_static(sample_code)
        dynamic_res = self.validator.analyze_dynamic(sample_code)
        verified_res = self.validator.verify_patch(sample_code)

        self.assertIsInstance(static_res, dict)
        self.assertIsInstance(dynamic_res, dict)
        self.assertIsInstance(verified_res, dict)
        self.assertTrue(verified_res.get("verified", False))

        stream_data = f"data_feed_{uuid.uuid4().hex}".encode('utf-8')
        stream_res_bytes = self.pipeline.verify_patch_stream(stream_data)
        self.assertTrue(stream_res_bytes.get("stream_verified", False))

        stream_res_io = self.validator.verify_stream(io.BytesIO(stream_data))
        self.assertTrue(stream_res_io.get("stream_verified", False))

    def test_ast_inspector_security_rules(self):
        forbidden_list = [f"unsafe_lib_{uuid.uuid4().hex[:6]}"]
        malicious_code = f"import {forbidden_list[0]}"

        inspector = ASTInspector(forbidden=forbidden_list)
        tree = compile(malicious_code, filename="<string>", mode="exec", flags=0, dont_inherit=True, optimize=-1)
        import ast as py_ast
        parsed_tree = py_ast.parse(malicious_code)

        with self.assertRaises(ValueError):
            inspector.visit(parsed_tree)

    def test_sandbox_execution_and_cve_fetching(self):
        var_name = f"var_{uuid.uuid4().hex[:6]}"
        var_value = random.randint(1000, 9999)
        code = f"{var_name} = {var_value}"

        exec_result = sandbox_exec(code)
        self.assertIsInstance(exec_result, dict)
        self.assertEqual(exec_result.get(var_name), var_value)

        valid_urls = [f"https://example.com/rss/{uuid.uuid4().hex}" for _ in range(random.randint(1, 3))]
        feeds = fetch_cve_feeds(valid_urls)
        self.assertEqual(feeds, [])

        invalid_url = f"https://invalid-feed.org/{uuid.uuid4().hex}"
        with self.assertRaises(ConnectionError):
            fetch_cve_feeds([invalid_url])

if __name__ == '__main__':
    unittest.main()