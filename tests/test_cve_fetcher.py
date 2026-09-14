import unittest
from unittest.mock import patch
import io
import uuid
import random
import string
import ast

from skills.cve_fetcher import (
    PipelineResult,
    ErrorRecoveryHub,
    PatchValidator,
    ASTInspector,
    AutoPatchPipeline,
    sandbox_exec,
    fetch_cve_feeds
)


class TestCVEFetcherModule(unittest.TestCase):

    def setUp(self):
        self.rand_str = lambda: uuid.uuid4().hex
        self.rand_num = lambda: random.randint(1000, 99999)
        self.module_name = f"module_{self.rand_str()}"
        self.incident_id = self.rand_str()
        self.error_msg = f"error_{self.rand_str()}"

    def test_pipeline_result_initialization(self):
        success = random.choice([True, False])
        incident_id = self.rand_str()
        error = self.error_msg if not success else None
        raw_result = {self.rand_str(): self.rand_str()}
        patch_data = {self.rand_str(): self.rand_str()}

        res = PipelineResult(
            success=success,
            incident_id=incident_id,
            error=error,
            raw_result=raw_result,
            patch_data=patch_data
        )

        self.assertEqual(res.success, success)
        self.assertEqual(res.incident_id, incident_id)
        self.assertEqual(res.error, error)
        self.assertEqual(res.raw_result, raw_result)
        self.assertEqual(res.patch_data, patch_data)

    def test_error_recovery_hub_capture_and_history(self):
        hub = ErrorRecoveryHub()
        exc = Exception(self.error_msg)
        tb_str = f"traceback_{self.rand_str()}"

        captured_id = hub.capture_failure(self.module_name, exc, tb_str)
        self.assertIsInstance(captured_id, str)
        self.assertTrue(len(captured_id) > 0)

        logs = hub.get_incident_logs(captured_id)
        self.assertEqual(logs["incident_id"], captured_id)
        self.assertEqual(logs["module_name"], self.module_name)
        self.assertEqual(logs["exception"], self.error_msg)
        self.assertEqual(logs["traceback"], tb_str)

        history = hub.get_incident_history(self.module_name)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["incident_id"], captured_id)

    def test_error_recovery_hub_workflow(self):
        hub = ErrorRecoveryHub()
        exc = Exception(self.error_msg)
        context = {self.rand_str(): self.rand_str()}

        analysis = hub.analyze_failure(self.incident_id)
        self.assertEqual(analysis["status"], "analyzed")
        self.assertEqual(analysis["incident_id"], self.incident_id)

        patch = hub.generate_patch(self.incident_id)
        self.assertIsInstance(patch, dict)

        applied = hub.apply_patch(patch)
        self.assertTrue(applied)

        deployed = hub.deploy_and_verify(self.incident_id, patch)
        self.assertTrue(deployed)

        result = hub.analyze_and_recover(self.module_name, exc, context)
        self.assertIsInstance(result, PipelineResult)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.incident_id)

    def test_patch_validator_methods(self):
        validator = PatchValidator()
        code_str = f"def {self.rand_str()}(): pass"

        static_res = validator.analyze_static(code_str)
        self.assertIn("static", static_res)

        dynamic_res = validator.analyze_dynamic(code_str)
        self.assertIn("dynamic", dynamic_res)

        verify_res = validator.verify_patch(code_str)
        self.assertTrue(verify_res.get("verified"))

        stream_data = io.BytesIO(code_str.encode('utf-8'))
        stream_res = validator.verify_stream(stream_data)
        self.assertTrue(stream_res.get("stream_verified"))

        val_res = validator.validate({self.rand_str(): self.rand_str()})
        self.assertTrue(val_res)

    def test_ast_inspector_forbidden_imports(self):
        forbidden_mod = f"bad_mod_{self.rand_str()}"
        inspector = ASTInspector(forbidden=[forbidden_mod])

        valid_code = f"import math\nx = math.pi"
        tree_valid = ast.parse(valid_code)

        try:
            inspector.visit(tree_valid)
        except Exception as e:
            self.fail(f"ASTInspector failed on valid import: {e}")

        invalid_code_1 = f"import {forbidden_mod}"
        tree_invalid_1 = ast.parse(invalid_code_1)
        with self.assertRaises(ValueError):
            inspector.visit(tree_invalid_1)

        invalid_code_2 = f"from {forbidden_mod} import something"
        tree_invalid_2 = ast.parse(invalid_code_2)
        with self.assertRaises(ValueError):
            inspector.visit(tree_invalid_2)

    def test_auto_patch_pipeline_run(self):
        pipeline = AutoPatchPipeline()
        exc = Exception(self.error_msg)
        context = {self.rand_str(): self.rand_str()}

        res = pipeline.run_pipeline(self.module_name, exc, f"tb_{self.rand_str()}", context)
        self.assertIsInstance(res, PipelineResult)
        self.assertTrue(res.success)
        self.assertIsInstance(res.incident_id, str)

    def test_auto_patch_pipeline_verify_stream(self):
        pipeline = AutoPatchPipeline()
        random_payload = f"print('{self.rand_str()}')"

        res_bytes = pipeline.verify_patch_stream(random_payload.encode('utf-8'))
        self.assertTrue(res_bytes.get("stream_verified"))

        res_str = pipeline.verify_patch_stream(random_payload)
        self.assertTrue(res_str.get("stream_verified"))

        stream_obj = io.BytesIO(random_payload.encode('utf-8'))
        res_io = pipeline.verify_patch_stream(stream_obj)
        self.assertTrue(res_io.get("stream_verified"))

    def test_auto_patch_pipeline_force_recover(self):
        pipeline = AutoPatchPipeline()
        exc = Exception(self.error_msg)
        context = {self.rand_str(): self.rand_str()}

        res = pipeline.force_analyze_and_recover(self.module_name, exc, context)
        self.assertIsInstance(res, PipelineResult)
        self.assertTrue(res.success)

    def test_sandbox_exec(self):
        var_name = f"var_{self.rand_str()}"
        var_val = self.rand_str()
        code = f"{var_name} = '{var_val}'"

        local_vars = sandbox_exec(code)
        self.assertIn(var_name, local_vars)
        self.assertEqual(local_vars[var_name], var_val)

    def test_fetch_cve_feeds_success(self):
        urls = [f"https://{self.rand_str()}.com/rss", f"https://{self.rand_str()}.org/xml"]
        res = fetch_cve_feeds(urls)
        self.assertEqual(res, [])

    def test_fetch_cve_feeds_failure(self):
        bad_url = f"https://invalid-{self.rand_str()}.com/feed"
        urls = [f"https://{self.rand_str()}.com/rss", bad_url]
        with self.assertRaises(ConnectionError):
            fetch_cve_feeds(urls)


if __name__ == '__main__':
    unittest.main()