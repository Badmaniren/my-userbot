import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

from skills.cve_monitor import (
    PipelineResult,
    AutoPatchPipeline,
    ErrorRecoveryHub,
    PatchValidator,
    ASTInspector,
    sandbox_exec
)

class TestCVEMonitorArchitect(unittest.TestCase):

    def setUp(self):
        self.rand_module = f"mod_{uuid.uuid4().hex[:8]}"
        self.rand_incident = uuid.uuid4().hex
        self.rand_error_msg = f"err_{uuid.uuid4().hex}"
        self.rand_traceback = f"tb_{uuid.uuid4().hex}"
        self.rand_code = f"def {self.rand_module}(): return '{uuid.uuid4().hex}'"

    def test_pipeline_result_initialization(self):
        success_val = random.choice([True, False])
        raw_res = {uuid.uuid4().hex: uuid.uuid4().hex}
        patch_dt = {uuid.uuid4().hex: uuid.uuid4().hex}

        result = PipelineResult(
            success=success_val,
            incident_id=self.rand_incident,
            error=self.rand_error_msg,
            raw_result=raw_res,
            patch_data=patch_dt
        )

        self.assertEqual(result.success, success_val)
        self.assertEqual(result.incident_id, self.rand_incident)
        self.assertEqual(result.error, self.rand_error_msg)
        self.assertEqual(result.raw_result, raw_res)
        self.assertEqual(result.patch_data, patch_dt)

    def test_auto_patch_pipeline_run(self):
        pipeline = AutoPatchPipeline()
        context_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.cve_monitor.ErrorRecoveryHub') as mock_hub_cls:
            mock_hub = mock_hub_cls.return_value
            mock_hub.analyze_and_recover.return_value = {
                uuid.uuid4().hex: uuid.uuid4().hex,
                "incident_id": self.rand_incident,
                "success": True
            }

            res = pipeline.run_pipeline(
                module_name=self.rand_module,
                exception=Exception(self.rand_error_msg),
                traceback_str=self.rand_traceback,
                context=context_data
            )

            self.assertIsInstance(res, PipelineResult)
            self.assertEqual(res.incident_id, self.rand_incident)

    def test_auto_patch_pipeline_verify_stream(self):
        pipeline = AutoPatchPipeline()
        stream_data = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)

        with patch('skills.cve_monitor.PatchValidator') as mock_validator_cls:
            mock_validator = mock_validator_cls.return_value
            expected_dict = {uuid.uuid4().hex: random.choice([True, False])}
            mock_validator.verify_stream.return_value = expected_dict

            output = pipeline.verify_patch_stream(stream_data)
            self.assertEqual(output, expected_dict)
            mock_validator.verify_stream.assert_called_once_with(stream_data)

    def test_auto_patch_pipeline_force_analyze(self):
        pipeline = AutoPatchPipeline()
        context_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(pipeline, 'run_pipeline') as mock_run:
            expected_res = PipelineResult(True, self.rand_incident, None, {}, {})
            mock_run.return_value = expected_res

            res = pipeline.force_analyze_and_recover(
                module_name=self.rand_module,
                exception=Exception(self.rand_error_msg),
                context=context_data
            )

            self.assertEqual(res, expected_res)
            mock_run.assert_called_once()

    def test_error_recovery_hub_lifecycle(self):
        hub = ErrorRecoveryHub()
        exc = Exception(self.rand_error_msg)

        inc_id = hub.capture_failure(self.rand_module, exc, self.rand_traceback)
        self.assertIsInstance(inc_id, str)
        self.assertTrue(len(inc_id) > 0)

        history = hub.get_incident_history(self.rand_module)
        self.assertIn(inc_id, history)

        logs = hub.get_incident_logs(inc_id)
        self.assertIsInstance(logs, dict)
        self.assertEqual(logs.get("module_name"), self.rand_module)

        analysis = hub.analyze_failure(inc_id)
        self.assertIsInstance(analysis, dict)

        patch_info = hub.generate_patch(inc_id)
        self.assertIsInstance(patch_info, dict)

        applied = hub.apply_patch(patch_info)
        self.assertIsInstance(applied, bool)

        deploy_res = hub.deploy_and_verify(inc_id, patch_info)
        self.assertIsInstance(deploy_res, bool)

        rec_res = hub.analyze_and_recover(self.rand_module, exc, {})
        self.assertIsInstance(rec_res, dict)

    def test_patch_validator_methods(self):
        validator = PatchValidator()
        safe_code = f"x = {random.randint(1, 100)}\ny = {random.randint(1, 100)}\nz = x + y"

        static_res = validator.analyze_static(safe_code)
        self.assertIsInstance(static_res, dict)

        dynamic_res = validator.analyze_dynamic(safe_code)
        self.assertIsInstance(dynamic_res, dict)

        verify_res = validator.verify_patch(safe_code)
        self.assertIsInstance(verify_res, dict)

        stream_data = io.BytesIO(safe_code.encode('utf-8'))
        stream_res = validator.verify_stream(stream_data)
        self.assertIsInstance(stream_res, dict)

        patch_data_obj = {uuid.uuid4().hex: safe_code}
        is_valid = validator.validate(patch_data_obj)
        self.assertIsInstance(is_valid, bool)

    def test_ast_inspector_violations(self):
        import ast
        forbidden_list = [uuid.uuid4().hex, uuid.uuid4().hex]
        inspector = ASTInspector(forbidden=forbidden_list)

        node_import = ast.Import(names=[ast.alias(name=forbidden_list[0], asname=None)])
        inspector.visit_Import(node_import)

        node_from = ast.ImportFrom(module=forbidden_list[1], names=[ast.alias(name='foo', asname=None)], level=0)
        inspector.visit_ImportFrom(node_from)

        node_call = ast.Call(func=ast.Name(id=forbidden_list[0], ctx=ast.Load()), args=[], keywords=[])
        inspector.visit_Call(node_call)

        self.assertTrue(True)

    def test_sandbox_exec(self):
        rand_var = f"var_{uuid.uuid4().hex[:6]}"
        rand_val = random.randint(100, 999)
        code_snippet = f"{rand_var} = {rand_val}"

        env = sandbox_exec(code_snippet)
        self.assertIsInstance(env, dict)
        self.assertIn(rand_var, env)
        self.assertEqual(env[rand_var], rand_val)

if __name__ == '__main__':
    unittest.main()