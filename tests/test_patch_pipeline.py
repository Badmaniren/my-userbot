import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
from skills.patch_pipeline import PatchPipeline, run_pipeline, PatchPipelineError
from skills.patch_sanitizer import PatchSanitizerError
from skills.patch_checker import PatchCheckerError
from skills.patch_applier import PatchApplierError

class TestPatchPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.target_file = f"src/{uuid.uuid4().hex}.py"
        self.policy = random.choice(["strict", "lenient", "custom"])
        self.raw_patch_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n+print('{uuid.uuid4().hex}')"

    @patch('skills.patch_applier.apply_patch')
    @patch('skills.patch_checker.check_patch')
    @patch('skills.patch_sanitizer.sanitize_patch')
    def test_pipeline_success_flow(self, mock_sanitize, mock_check, mock_apply):
        sanitized_data = f"SANITIZED_{uuid.uuid4().hex}"
        mock_sanitize.return_value = sanitized_data
        mock_check.return_value = {"status": "passed"}
        mock_apply.return_value = True

        stream = io.BytesIO(self.raw_patch_content.encode('utf-8'))
        pipeline = PatchPipeline(repo_path=self.repo_path)
        result = pipeline.process_patch(stream, self.target_file, self.policy)

        self.assertTrue(result)
        mock_sanitize.assert_called_once()
        mock_check.assert_called_once_with(sanitized_data, self.repo_path, self.target_file, self.policy)
        mock_apply.assert_called_once_with(self.repo_path, sanitized_data)

    @patch('skills.patch_sanitizer.sanitize_patch')
    def test_pipeline_sanitizer_error(self, mock_sanitize):
        err_msg = f"Sanitization failed {uuid.uuid4().hex}"
        mock_sanitize.side_effect = PatchSanitizerError(err_msg)

        stream = io.BytesIO(self.raw_patch_content.encode('utf-8'))
        pipeline = PatchPipeline(repo_path=self.repo_path)

        with self.assertRaises(PatchPipelineError) as ctx:
            pipeline.process_patch(stream, self.target_file, self.policy)
        self.assertIn(err_msg, str(ctx.exception))

    @patch('skills.patch_checker.check_patch')
    @patch('skills.patch_sanitizer.sanitize_patch')
    def test_pipeline_checker_error_exception(self, mock_sanitize, mock_check):
        err_msg = f"Checker exception {uuid.uuid4().hex}"
        mock_sanitize.return_value = "clean patch"
        mock_check.side_effect = PatchCheckerError(err_msg)

        stream = io.BytesIO(self.raw_patch_content.encode('utf-8'))
        pipeline = PatchPipeline(repo_path=self.repo_path)

        with self.assertRaises(PatchPipelineError) as ctx:
            pipeline.process_patch(stream, self.target_file, self.policy)
        self.assertIn(err_msg, str(ctx.exception))

    @patch('skills.patch_checker.check_patch')
    @patch('skills.patch_sanitizer.sanitize_patch')
    def test_pipeline_checker_policy_violation(self, mock_sanitize, mock_check):
        violation_reason = f"Policy violation reason {uuid.uuid4().hex}"
        mock_sanitize.return_value = "clean patch"
        mock_check.return_value = {"status": "failed", "errors": [violation_reason]}

        stream = io.BytesIO(self.raw_patch_content.encode('utf-8'))
        pipeline = PatchPipeline(repo_path=self.repo_path)

        with self.assertRaises(PatchPipelineError) as ctx:
            pipeline.process_patch(stream, self.target_file, self.policy)
        self.assertIn(violation_reason, str(ctx.exception))

    @patch('skills.patch_applier.apply_patch')
    @patch('skills.patch_checker.check_patch')
    @patch('skills.patch_sanitizer.sanitize_patch')
    def test_pipeline_applier_returns_false(self, mock_sanitize, mock_check, mock_apply):
        mock_sanitize.return_value = "clean patch"
        mock_check.return_value = {"status": "passed"}
        mock_apply.return_value = False

        stream = io.BytesIO(self.raw_patch_content.encode('utf-8'))
        pipeline = PatchPipeline(repo_path=self.repo_path)

        with self.assertRaises(PatchPipelineError) as ctx:
            pipeline.process_patch(stream, self.target_file, self.policy)
        self.assertIn("Patch applier returned False", str(ctx.exception))

    @patch('skills.patch_applier.apply_patch')
    @patch('skills.patch_checker.check_patch')
    @patch('skills.patch_sanitizer.sanitize_patch')
    def test_pipeline_applier_error_exception(self, mock_sanitize, mock_check, mock_apply):
        err_msg = f"Applier crash {uuid.uuid4().hex}"
        mock_sanitize.return_value = "clean patch"
        mock_check.return_value = {"status": "passed"}
        mock_apply.side_effect = PatchApplierError(err_msg)

        stream = io.BytesIO(self.raw_patch_content.encode('utf-8'))
        pipeline = PatchPipeline(repo_path=self.repo_path)

        with self.assertRaises(PatchPipelineError) as ctx:
            pipeline.process_patch(stream, self.target_file, self.policy)
        self.assertIn(err_msg, str(ctx.exception))

    @patch('skills.patch_sanitizer.sanitize_patch')
    def test_pipeline_unexpected_exception(self, mock_sanitize):
        unexpected_msg = f"Unexpected failure {uuid.uuid4().hex}"
        mock_sanitize.side_effect = RuntimeError(unexpected_msg)

        stream = io.BytesIO(self.raw_patch_content.encode('utf-8'))
        pipeline = PatchPipeline(repo_path=self.repo_path)

        with self.assertRaises(PatchPipelineError) as ctx:
            pipeline.process_patch(stream, self.target_file, self.policy)
        self.assertIn("Unexpected pipeline error", str(ctx.exception))
        self.assertIn(unexpected_msg, str(ctx.exception))

    @patch('skills.patch_applier.apply_patch')
    @patch('skills.patch_checker.check_patch')
    @patch('skills.patch_sanitizer.sanitize_patch')
    def test_run_pipeline_with_string_input(self, mock_sanitize, mock_check, mock_apply):
        mock_sanitize.return_value = "sanitized string"
        mock_check.return_value = {"status": "passed"}
        mock_apply.return_value = True

        patch_str = f"diff string {uuid.uuid4().hex}"
        result = run_pipeline(patch_str, self.repo_path, self.target_file, self.policy)
        self.assertTrue(result)
        mock_sanitize.assert_called_once()

    @patch('skills.patch_applier.apply_patch')
    @patch('skills.patch_checker.check_patch')
    @patch('skills.patch_sanitizer.sanitize_patch')
    def test_run_pipeline_with_bytes_input(self, mock_sanitize, mock_check, mock_apply):
        mock_sanitize.return_value = "sanitized bytes"
        mock_check.return_value = {"status": "passed"}
        mock_apply.return_value = True

        patch_bytes = f"diff bytes {uuid.uuid4().hex}".encode('utf-8')
        result = run_pipeline(patch_bytes, self.repo_path, self.target_file, self.policy)
        self.assertTrue(result)
        mock_sanitize.assert_called_once()

    @patch('skills.patch_applier.apply_patch')
    @patch('skills.patch_checker.check_patch')
    @patch('skills.patch_sanitizer.sanitize_patch')
    def test_run_pipeline_with_invalid_type_input(self, mock_sanitize, mock_check, mock_apply):
        mock_sanitize.return_value = "sanitized fallback"
        mock_check.return_value = {"status": "passed"}
        mock_apply.return_value = True

        invalid_input = random.randint(1000, 9999)
        result = run_pipeline(invalid_input, self.repo_path, self.target_file, self.policy)
        self.assertTrue(result)
        mock_sanitize.assert_called_once()

if __name__ == '__main__':
    unittest.main()