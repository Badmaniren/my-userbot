import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import traceback
from skills.patch_auto_executor import PatchAutoExecutor, ExecutionResult

class TestPatchAutoExecutor(unittest.TestCase):

    def setUp(self):
        self.module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.exception_msg = f"Err_{uuid.uuid4().hex[:6]}"
        self.exception_obj = RuntimeError(self.exception_msg)
        self.traceback_str = "".join(traceback.format_tb(self.exception_obj.__traceback__)) if self.exception_obj.__traceback__ else f"Traceback {uuid.uuid4().hex}"
        self.context = {f"key_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex for _ in range(3)}
        self.incident_id = uuid.uuid4().hex
        self.patch_data = {f"patch_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex}
        self.stream_data = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)

    def test_executor_initialization(self):
        with patch('skills.patch_auto_executor.AutoPatchPipeline') as mock_pipeline_cls, \
             patch('skills.patch_auto_executor.ErrorRecoveryHub') as mock_hub_cls:
            
            mock_pipeline_instance = MagicMock()
            mock_hub_instance = MagicMock()
            mock_pipeline_cls.return_value = mock_pipeline_instance
            mock_hub_cls.return_value = mock_hub_instance

            executor = PatchAutoExecutor()

            self.assertEqual(executor.pipeline, mock_pipeline_instance)
            self.assertEqual(executor.hub, mock_hub_instance)
            mock_pipeline_cls.assert_called_once()
            mock_hub_cls.assert_called_once()

    def test_execute_auto_patch_success(self):
        with patch('skills.patch_auto_executor.AutoPatchPipeline') as mock_pipeline_cls, \
             patch('skills.patch_auto_executor.ErrorRecoveryHub') as mock_hub_cls:
            
            mock_pipeline_instance = MagicMock()
            mock_pipeline_cls.return_value = mock_pipeline_instance

            expected_result = MagicMock()
            expected_result.success = True
            expected_result.incident_id = self.incident_id
            expected_result.error = None
            expected_result.patch_data = self.patch_data
            mock_pipeline_instance.run_pipeline.return_value = expected_result

            executor = PatchAutoExecutor()
            result = executor.execute_auto_patch(self.module_name, self.exception_obj, self.traceback_str, self.context)

            mock_pipeline_instance.run_pipeline.assert_called_once_with(
                self.module_name, self.exception_obj, self.traceback_str, self.context
            )
            self.assertTrue(result.success)
            self.assertEqual(result.incident_id, self.incident_id)
            self.assertEqual(result.patch_data, self.patch_data)

    def test_execute_auto_patch_failure_fallback(self):
        with patch('skills.patch_auto_executor.AutoPatchPipeline') as mock_pipeline_cls, \
             patch('skills.patch_auto_executor.ErrorRecoveryHub') as mock_hub_cls:
            
            mock_pipeline_instance = MagicMock()
            mock_hub_instance = MagicMock()
            mock_pipeline_cls.return_value = mock_pipeline_instance
            mock_hub_cls.return_value = mock_hub_instance

            mock_pipeline_instance.run_pipeline.side_effect = Exception(uuid.uuid4().hex)
            
            fallback_result = MagicMock()
            fallback_result.success = False
            fallback_result.incident_id = self.incident_id
            fallback_result.patch_data = {}
            mock_hub_instance.analyze_and_recover.return_value = fallback_result

            executor = PatchAutoExecutor()
            result = executor.execute_auto_patch(self.module_name, self.exception_obj, self.traceback_str, self.context)

            mock_hub_instance.analyze_and_recover.assert_called_once_with(
                self.module_name, self.exception_obj, self.context
            )
            self.assertFalse(result.success)
            self.assertEqual(result.incident_id, self.incident_id)

    def test_verify_stream_delegation(self):
        with patch('skills.patch_auto_executor.AutoPatchPipeline') as mock_pipeline_cls, \
             patch('skills.patch_auto_executor.ErrorRecoveryHub') as mock_hub_cls:
            
            mock_pipeline_instance = MagicMock()
            mock_pipeline_cls.return_value = mock_pipeline_instance
            expected_verification = random.choice([True, False])
            mock_pipeline_instance.verify_patch_stream.return_value = expected_verification

            executor = PatchAutoExecutor()
            res = executor.verify_stream(self.stream_data)

            mock_pipeline_instance.verify_patch_stream.assert_called_once_with(self.stream_data)
            self.assertEqual(res, expected_verification)

    def test_force_recovery_pipeline(self):
        with patch('skills.patch_auto_executor.AutoPatchPipeline') as mock_pipeline_cls, \
             patch('skills.patch_auto_executor.ErrorRecoveryHub') as mock_hub_cls:
            
            mock_pipeline_instance = MagicMock()
            mock_pipeline_cls.return_value = mock_pipeline_instance
            
            expected_res = MagicMock()
            expected_res.success = True
            expected_res.incident_id = self.incident_id
            mock_pipeline_instance.force_analyze_and_recover.return_value = expected_res

            executor = PatchAutoExecutor()
            result = executor.force_recovery(self.module_name, self.exception_obj, self.context)

            mock_pipeline_instance.force_analyze_and_recover.assert_called_once_with(
                self.module_name, self.exception_obj, self.context
            )
            self.assertTrue(result.success)
            self.assertEqual(result.incident_id, self.incident_id)

    def test_hub_direct_capture_failure(self):
        with patch('skills.patch_auto_executor.AutoPatchPipeline') as mock_pipeline_cls, \
             patch('skills.patch_auto_executor.ErrorRecoveryHub') as mock_hub_cls:
            
            mock_hub_instance = MagicMock()
            mock_hub_cls.return_value = mock_hub_instance
            mock_hub_instance.capture_failure.return_value = self.incident_id

            executor = PatchAutoExecutor()
            inc_id = executor.capture_incident(self.module_name, self.exception_obj, self.traceback_str)

            mock_hub_instance.capture_failure.assert_called_once_with(
                self.module_name, self.exception_obj, self.traceback_str
            )
            self.assertEqual(inc_id, self.incident_id)

    def test_hub_deploy_and_verify(self):
        with patch('skills.patch_auto_executor.AutoPatchPipeline') as mock_pipeline_cls, \
             patch('skills.patch_auto_executor.ErrorRecoveryHub') as mock_hub_cls:
            
            mock_hub_instance = MagicMock()
            mock_hub_cls.return_value = mock_hub_instance
            deploy_status = random.choice([True, False])
            mock_hub_instance.deploy_and_verify.return_value = deploy_status

            executor = PatchAutoExecutor()
            status = executor.deploy_patch_payload(self.incident_id, self.patch_data)

            mock_hub_instance.deploy_and_verify.assert_called_once_with(
                self.incident_id, self.patch_data
            )
            self.assertEqual(status, deploy_status)