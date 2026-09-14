import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import traceback
from skills.patch_journal import (
    PipelineResult,
    AutoPatchPipeline,
    ErrorRecoveryHub,
    PatchValidator,
    ASTInspector,
    sandbox_exec
)

class TestPatchJournalArchitecture(unittest.TestCase):

    def setUp(self):
        self.rand_module = f"module_{uuid.uuid4().hex[:8]}"
        self.rand_incident_id = uuid.uuid4().hex
        self.rand_error_msg = f"CriticalError_{uuid.uuid4().hex[:6]}"
        self.rand_traceback = f"Traceback (most recent call last):\n  File \"{uuid.uuid4().hex}.py\", line {random.randint(1, 100)}, in <module>\n    raise Exception('{self.rand_error_msg}')"
        self.rand_code = f"def {uuid.uuid4().hex[:8]}():\n    x = {random.randint(10, 100)}\n    return x * {random.randint(2, 5)}"

    def test_pipeline_result_initialization(self):
        success = random.choice([True, False])
        raw_res = {"status": uuid.uuid4().hex}
        patch_dat = {"patch": uuid.uuid4().hex}
        
        res = PipelineResult(
            success=success,
            incident_id=self.rand_incident_id,
            error=self.rand_error_msg,
            raw_result=raw_res,
            patch_data=patch_dat
        )

        self.assertEqual(res.success, success)
        self.assertEqual(res.incident_id, self.rand_incident_id)
        self.assertEqual(res.error, self.rand_error_msg)
        self.assertEqual(res.raw_result, raw_res)
        self.assertEqual(res.patch_data, patch_dat)

    @patch('skills.patch_journal.ErrorRecoveryHub')
    @patch('skills.patch_journal.PatchValidator')
    def test_auto_patch_pipeline_run(self, mock_validator_cls, mock_hub_cls):
        mock_hub = mock_hub_cls.return_value
        mock_hub.analyze_and_recover.return_value = {
            "incident_id": self.rand_incident_id,
            "success": True,
            "patch": self.rand_code
        }

        pipeline = AutoPatchPipeline()
        context = {uuid.uuid4().hex: uuid.uuid4().hex}
        
        result = pipeline.run_pipeline(
            module_name=self.rand_module,
            exception=Exception(self.rand_error_msg),
            traceback_str=self.rand_traceback,
            context=context
        )

        self.assertIsInstance(result, PipelineResult)
        self.assertTrue(result.success)
        self.assertEqual(result.incident_id, self.rand_incident_id)
        mock_hub.analyze_and_recover.assert_called_once_with(self.rand_module, Exception(self.rand_error_msg), context)

    def test_verify_patch_stream(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)
        pipeline = AutoPatchPipeline()
        
        with patch('skills.patch_journal.PatchValidator') as mock_val_cls:
            mock_val = mock_val_cls.return_value
            expected_dict = {"verified": True, "token": uuid.uuid4().hex}
            mock_val.verify_stream.return_value = expected_dict

            res = pipeline.verify_patch_stream(stream_data)
            self.assertEqual(res, expected_dict)
            mock_val.verify_stream.assert_called_once_with(stream_data)

    def test_force_analyze_and_recover(self):
        pipeline = AutoPatchPipeline()
        context = {uuid.uuid4().hex: random.randint(1, 500)}
        
        with patch.object(pipeline, 'run_pipeline') as mock_run:
            mock_run.return_value = PipelineResult(True, self.rand_incident_id, None, {}, {})
            
            res = pipeline.force_analyze_and_recover(
                module_name=self.rand_module,
                exception=Exception(self.rand_error_msg),
                context=context
            )
            
            self.assertTrue(res.success)
            mock_run.assert_called_once()

    def test_error_recovery_hub_lifecycle(self):
        hub = ErrorRecoveryHub()
        
        inc_id = hub.capture_failure(self.rand_module, Exception(self.rand_error_msg), self.rand_traceback)
        self.assertIsInstance(inc_id, str)
        self.assertTrue(len(inc_id) > 0)

        history = hub.get_incident_history(self.rand_module)
        self.assertIsInstance(history, list)

        logs = hub.get_incident_logs(inc_id)
        self.assertIsInstance(logs, (dict, list, str, type(None)))

        analysis = hub.analyze_failure(inc_id)
        self.assertIsInstance(analysis, dict)

        patch_data = hub.generate_patch(inc_id)
        self.assertIsInstance(patch_data, (dict, str))

        apply_res = hub.apply_patch(patch_data)
        self.assertIn(type(apply_res), [bool, dict])

    def test_patch_validator_suite(self):
        validator = PatchValidator()
        
        static_res = validator.analyze_static(self.rand_code)
        self.assertIsInstance(static_res, dict)

        dynamic_res = validator.analyze_dynamic(self.rand_code)
        self.assertIsInstance(dynamic_res, dict)

        verify_res = validator.verify_patch(self.rand_code)
        self.assertIsInstance(verify_res, dict)

        stream = io.BytesIO(self.rand_code.encode('utf-8'))
        stream_res = validator.verify_stream(stream)
        self.assertIsInstance(stream_res, dict)

        is_valid = validator.validate({"code": self.rand_code})
        self.assertIsInstance(is_valid, bool)

    def test_ast_inspector_visitor(self):
        forbidden_list = [uuid.uuid4().hex, uuid.uuid4().hex]
        inspector = ASTInspector(forbidden=forbidden_list)
        
        mock_node = MagicMock()
        try:
            inspector.visit_Import(mock_node)
            inspector.visit_ImportFrom(mock_node)
            inspector.visit_Call(mock_node)
        except Exception as e:
            self.fail(f"ASTInspector methods raised unexpected exception: {e}")

    def test_sandbox_exec_stub(self):
        res = sandbox_exec(self.rand_code)
        self.assertIsInstance(res, (dict, bool, type(None)))

    def test_deploy_and_verify_in_hub(self):
        hub = ErrorRecoveryHub()
        inc_id = hub.capture_failure(self.rand_module, Exception(self.rand_error_msg), self.rand_traceback)
        payload = {uuid.uuid4().hex: self.rand_code}
        
        res = hub.deploy_and_verify(inc_id, payload)
        self.assertIsInstance(res, (bool, dict))

    def test_analyze_and_recover_in_hub(self):
        hub = ErrorRecoveryHub()
        context = {uuid.uuid4().hex: uuid.uuid4().hex}
        
        res = hub.analyze_and_recover(self.rand_module, Exception(self.rand_error_msg), context)
        self.assertIsInstance(res, dict)