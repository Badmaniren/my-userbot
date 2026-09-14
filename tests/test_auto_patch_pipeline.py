import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys

from skills.auto_patch_pipeline import AutoPatchPipeline, PipelineResult


class TestAutoPatchPipelineInquisitor(unittest.TestCase):

    def setUp(self):
        self.module_name = f"mod_{uuid.uuid4().hex[:8]}"
        self.exception_msg = f"Err_{uuid.uuid4().hex[:6]}"
        self.traceback_str = f"Traceback at {uuid.uuid4().hex}"
        self.incident_id = f"inc_{uuid.uuid4().hex[:8]}"
        self.patch_code = f"def fix_{uuid.uuid4().hex[:4]}(): pass"
        self.pipeline = AutoPatchPipeline()

    def test_composition_dependencies_import(self):
        self.assertTrue(
            hasattr(self.pipeline, 'error_recovery_hub'),
            "Архитектурный сбой: AutoPatchPipeline обязан инстанцировать ErrorRecoveryHub"
        )
        self.assertTrue(
            hasattr(self.pipeline, 'patch_validator'),
            "Архитектурный сбой: AutoPatchPipeline обязан инстанцировать PatchValidator"
        )

    def test_run_pipeline_success_flow(self):
        exc = RuntimeError(self.exception_msg)
        context_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        
        with patch.object(self.pipeline.error_recovery_hub, 'capture_failure', return_value=self.incident_id) as mock_capture, \
             patch.object(self.pipeline.error_recovery_hub, 'generate_patch', return_value={'code': self.patch_code, 'id': self.incident_id}) as mock_gen, \
             patch.object(self.pipeline.patch_validator, 'validate', return_value=True) as mock_val, \
             patch.object(self.pipeline.error_recovery_hub, 'deploy_and_verify', return_value=True) as mock_deploy:

            result = self.pipeline.run_pipeline(self.module_name, exc, self.traceback_str, context_data)

            mock_capture.assert_called_once_with(self.module_name, exc, self.traceback_str)
            mock_gen.assert_called_once_with(self.incident_id)
            mock_val.assert_called_once()
            mock_deploy.assert_called_once()
            
            self.assertTrue(result.success, f"Конвейер должен завершиться успехом для инцидента {self.incident_id}")
            self.assertEqual(result.incident_id, self.incident_id)

    def test_run_pipeline_validation_failure(self):
        exc = ValueError(self.exception_msg)
        
        with patch.object(self.pipeline.error_recovery_hub, 'capture_failure', return_value=self.incident_id) as mock_capture, \
             patch.object(self.pipeline.error_recovery_hub, 'generate_patch', return_value={'code': self.patch_code}) as mock_gen, \
             patch.object(self.pipeline.patch_validator, 'validate', return_value=False) as mock_val, \
             patch.object(self.pipeline.error_recovery_hub, 'deploy_and_verify') as mock_deploy:

            result = self.pipeline.run_pipeline(self.module_name, exc, self.traceback_str)

            mock_capture.assert_called_once()
            mock_gen.assert_called_once_with(self.incident_id)
            mock_val.assert_called_once()
            mock_deploy.assert_not_called()
            
            self.assertFalse(result.success, "Патч не прошедший валидацию не должен деплоиться")
            self.assertIn("validation failed", result.error.lower())

    def test_run_pipeline_generation_fails(self):
        exc = TypeError(self.exception_msg)
        
        with patch.object(self.pipeline.error_recovery_hub, 'capture_failure', return_value=self.incident_id), \
             patch.object(self.pipeline.error_recovery_hub, 'generate_patch', return_value=None) as mock_gen, \
             patch.object(self.pipeline.patch_validator, 'validate') as mock_val:

            result = self.pipeline.run_pipeline(self.module_name, exc, self.traceback_str)

            mock_gen.assert_called_once_with(self.incident_id)
            mock_val.assert_not_called()
            self.assertFalse(result.success)

    def test_stream_verification_integration(self):
        random_bytes = ''.join(random.choices(string.ascii_letters, k=32)).encode('utf-8')
        stream = io.BytesIO(random_bytes)
        expected_dict = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch.object(self.pipeline.patch_validator, 'verify_stream', return_value=expected_dict) as mock_verify_stream:
            res = self.pipeline.verify_patch_stream(stream)
            mock_verify_stream.assert_called_once_with(stream)
            self.assertEqual(res, expected_dict)

    def test_analyze_and_recover_delegation(self):
        exc = ZeroDivisionError(self.exception_msg)
        context = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_return = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.pipeline.error_recovery_hub, 'analyze_and_recover', return_value=expected_return) as mock_analyze:
            res = self.pipeline.force_analyze_and_recover(self.module_name, exc, context)
            mock_analyze.assert_called_once_with(self.module_name, exc, context)
            self.assertEqual(res, expected_return)