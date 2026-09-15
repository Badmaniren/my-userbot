import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.auto_patch_pipeline import AutoPatchPipeline, PipelineResult


class TestPipelineResult(unittest.TestCase):
    def test_pipeline_result_success_state(self):
        rand_incident = uuid.uuid4().hex
        rand_raw = uuid.uuid4().hex
        rand_patch = {"patch_id": uuid.uuid4().hex}

        res = PipelineResult(
            success=True,
            incident_id=rand_incident,
            raw_result=rand_raw,
            patch_data=rand_patch
        )

        self.assertTrue(res.success)
        self.assertEqual(res.incident_id, rand_incident)
        self.assertIsNone(res.error)
        self.assertEqual(res.raw_result, rand_raw)
        self.assertEqual(res.patch_data, rand_patch)

        self.assertTrue(res["success"])
        self.assertEqual(res["incident_id"], rand_incident)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["patch_data"], rand_patch)
        self.assertIn("incident_id", res)
        self.assertIn("status", res)
        self.assertIn("patch_data", res)
        self.assertIn("success", res)
        self.assertIn("error", res)

    def test_pipeline_result_failure_state(self):
        rand_incident = uuid.uuid4().hex
        rand_error = "".join(random.choices(string.ascii_letters, k=15))
        rand_patch = {"bad_patch": uuid.uuid4().hex}

        res = PipelineResult(
            success=False,
            incident_id=rand_incident,
            error=rand_error,
            patch_data=rand_patch
        )

        self.assertFalse(res.success)
        self.assertEqual(res.incident_id, rand_incident)
        self.assertEqual(res.error, rand_error)
        self.assertEqual(res.patch_data, rand_patch)

        self.assertFalse(res["success"])
        self.assertEqual(res["incident_id"], rand_incident)
        self.assertEqual(res["status"], "failed")
        self.assertEqual(res["error"], rand_error)
        self.assertEqual(res["patch_data"], rand_patch)


class TestAutoPatchPipeline(unittest.TestCase):
    def test_run_pipeline_success_flow(self):
        pipeline = AutoPatchPipeline()
        rand_module = uuid.uuid4().hex
        rand_exception = ValueError("".join(random.choices(string.ascii_letters, k=10)))
        rand_tb = uuid.uuid4().hex
        rand_incident_id = uuid.uuid4().hex
        rand_patch_data = {"code": uuid.uuid4().hex}
        rand_deploy_res = uuid.uuid4().hex

        with patch.object(pipeline.error_recovery_hub, 'capture_failure', return_value=rand_incident_id) as mock_capture, \
             patch.object(pipeline.error_recovery_hub, 'generate_patch', return_value=rand_patch_data) as mock_gen, \
             patch.object(pipeline.patch_validator, 'validate', return_value=True) as mock_val, \
             patch.object(pipeline.error_recovery_hub, 'deploy_and_verify', return_value=rand_deploy_res) as mock_deploy:

            result = pipeline.run_pipeline(rand_module, rand_exception, rand_tb)

            mock_capture.assert_called_once_with(rand_module, rand_exception, rand_tb)
            mock_gen.assert_called_once_with(rand_incident_id)
            mock_val.assert_called_once_with(rand_patch_data)
            mock_deploy.assert_called_once_with(rand_patch_data)

            self.assertTrue(result.success)
            self.assertEqual(result.incident_id, rand_incident_id)
            self.assertEqual(result.patch_data, rand_patch_data)
            self.assertEqual(result.raw_result, rand_deploy_res)
            self.assertIsNone(result.error)

    def test_run_pipeline_capture_failure_exception_fallback(self):
        pipeline = AutoPatchPipeline()
        rand_module = uuid.uuid4().hex
        rand_exception = RuntimeError("".join(random.choices(string.ascii_letters, k=12)))
        rand_tb = uuid.uuid4().hex
        rand_patch_data = {"patch": uuid.uuid4().hex}

        with patch.object(pipeline.error_recovery_hub, 'capture_failure', side_effect=Exception("Crash")) as mock_capture, \
             patch.object(pipeline.error_recovery_hub, 'generate_patch', return_value=rand_patch_data) as mock_gen, \
             patch.object(pipeline.patch_validator, 'validate', return_value=True) as mock_val, \
             patch.object(pipeline.error_recovery_hub, 'deploy_and_verify', return_value=True):

            result = pipeline.run_pipeline(rand_module, rand_exception, rand_tb)

            mock_capture.assert_called_once_with(rand_module, rand_exception, rand_tb)
            self.assertTrue(result.success)
            self.assertTrue(result.incident_id.startswith("inc_fallback_"))
            self.assertEqual(result.patch_data, rand_patch_data)

    def test_run_pipeline_generation_failure(self):
        pipeline = AutoPatchPipeline()
        rand_module = uuid.uuid4().hex
        rand_exception = TypeError("".join(random.choices(string.ascii_letters, k=8)))
        rand_tb = uuid.uuid4().hex
        rand_incident_id = uuid.uuid4().hex

        with patch.object(pipeline.error_recovery_hub, 'capture_failure', return_value=rand_incident_id), \
             patch.object(pipeline.error_recovery_hub, 'generate_patch', side_effect=Exception("Gen fail")) as mock_gen:

            result = pipeline.run_pipeline(rand_module, rand_exception, rand_tb)

            mock_gen.assert_called_once_with(rand_incident_id)
            self.assertFalse(result.success)
            self.assertEqual(result.incident_id, rand_incident_id)
            self.assertEqual(result.error, "Generation failed")
            self.assertIsNone(result.patch_data)

    def test_run_pipeline_validation_failure(self):
        pipeline = AutoPatchPipeline()
        rand_module = uuid.uuid4().hex
        rand_exception = KeyError("".join(random.choices(string.ascii_letters, k=9)))
        rand_tb = uuid.uuid4().hex
        rand_incident_id = uuid.uuid4().hex
        rand_patch_data = {"invalid": uuid.uuid4().hex}

        with patch.object(pipeline.error_recovery_hub, 'capture_failure', return_value=rand_incident_id), \
             patch.object(pipeline.error_recovery_hub, 'generate_patch', return_value=rand_patch_data), \
             patch.object(pipeline.patch_validator, 'validate', return_value=False) as mock_val:

            result = pipeline.run_pipeline(rand_module, rand_exception, rand_tb)

            mock_val.assert_called_once_with(rand_patch_data)
            self.assertFalse(result.success)
            self.assertEqual(result.incident_id, rand_incident_id)
            self.assertEqual(result.error, "Validation failed")
            self.assertEqual(result.patch_data, rand_patch_data)

    def test_run_pipeline_deployment_exception_handling(self):
        pipeline = AutoPatchPipeline()
        rand_module = uuid.uuid4().hex
        rand_exception = ZeroDivisionError("".join(random.choices(string.ascii_letters, k=10)))
        rand_tb = uuid.uuid4().hex
        rand_incident_id = uuid.uuid4().hex
        rand_patch_data = {"patch_x": uuid.uuid4().hex}
        rand_deploy_error = uuid.uuid4().hex

        with patch.object(pipeline.error_recovery_hub, 'capture_failure', return_value=rand_incident_id), \
             patch.object(pipeline.error_recovery_hub, 'generate_patch', return_value=rand_patch_data), \
             patch.object(pipeline.patch_validator, 'validate', return_value=True), \
             patch.object(pipeline.error_recovery_hub, 'deploy_and_verify', side_effect=Exception(rand_deploy_error)) as mock_deploy:

            result = pipeline.run_pipeline(rand_module, rand_exception, rand_tb)

            mock_deploy.assert_called_once_with(rand_patch_data)
            self.assertTrue(result.success)
            self.assertEqual(result.incident_id, rand_incident_id)
            self.assertEqual(result.patch_data, rand_patch_data)
            self.assertEqual(result.raw_result, rand_deploy_error)

    def test_verify_patch_stream(self):
        pipeline = AutoPatchPipeline()
        rand_stream = uuid.uuid4().hex
        rand_validation_result = random.choice([True, False])

        with patch.object(pipeline.patch_validator, 'verify_stream', return_value=rand_validation_result) as mock_verify:
            res = pipeline.verify_patch_stream(rand_stream)
            mock_verify.assert_called_once_with(rand_stream)
            self.assertEqual(res, rand_validation_result)

    def test_force_analyze_and_recover(self):
        pipeline = AutoPatchPipeline()
        rand_module = uuid.uuid4().hex
        rand_exception = SyntaxError("".join(random.choices(string.ascii_letters, k=11)))
        rand_context = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_recovery_res = {"status": uuid.uuid4().hex}

        with patch.object(pipeline.error_recovery_hub, 'analyze_and_recover', return_value=rand_recovery_res) as mock_analyze:
            res = pipeline.force_analyze_and_recover(rand_module, rand_exception, rand_context)
            mock_analyze.assert_called_once_with(rand_module, rand_exception, rand_context)
            self.assertEqual(res, rand_recovery_res)