import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

from skills.patch_pipeline_executor import (
    execute_patch_pipeline,
    execute_pipeline,
    PatchPipelineError,
)
from skills.patch_sanitizer import PatchSanitizerError
from skills.patch_applier import PatchApplierError


class TestPatchPipelineExecutorInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.backup_tag = f"backup_{uuid.uuid4().hex}"
        self.raw_patch_content = f"diff --git a/{uuid.uuid4().hex}.py b/{uuid.uuid4().hex}.py\n+print('{uuid.uuid4().hex}')"
        self.sanitized_patch_content = f"sanitized_diff_{uuid.uuid4().hex}"

    @patch("skills.patch_pipeline_executor.PatchApplier")
    @patch("skills.patch_pipeline_executor.PatchSanitizer")
    def test_execute_patch_pipeline_success(self, mock_sanitizer_cls, mock_applier_cls):
        mock_sanitizer = mock_sanitizer_cls.return_value
        mock_sanitizer.sanitize.return_value = self.sanitized_patch_content

        mock_applier = mock_applier_cls.return_value
        mock_applier.apply_patch.return_value = True

        stream_input = io.StringIO(self.raw_patch_content)
        result = execute_patch_pipeline(self.repo_path, stream_input, backup_tag=self.backup_tag)

        self.assertTrue(result)
        mock_sanitizer.sanitize.assert_called_once_with(stream_input)
        mock_applier_cls.assert_called_once_with(repo_path=self.repo_path)
        mock_applier.create_recovery_point.assert_called_once_with(self.backup_tag)
        mock_applier.apply_patch.assert_called_once()

    @patch("skills.patch_pipeline_executor.PatchApplier")
    @patch("skills.patch_pipeline_executor.PatchSanitizer")
    def test_execute_pipeline_alias_success(self, mock_sanitizer_cls, mock_applier_cls):
        mock_sanitizer = mock_sanitizer_cls.return_value
        mock_sanitizer.sanitize.return_value = self.sanitized_patch_content

        mock_applier = mock_applier_cls.return_value
        mock_applier.apply_patch.return_value = True

        stream_input = io.StringIO(self.raw_patch_content)
        result = execute_pipeline(self.repo_path, stream_input, backup_tag=None)

        self.assertTrue(result)
        mock_applier.create_recovery_point.assert_not_called()
        mock_applier.apply_patch.assert_called_once()

    @patch("skills.patch_pipeline_executor.PatchSanitizer")
    def test_execute_patch_pipeline_sanitization_error(self, mock_sanitizer_cls):
        error_message = f"Sanitizer failed {uuid.uuid4().hex}"
        mock_sanitizer = mock_sanitizer_cls.return_value
        mock_sanitizer.sanitize.side_effect = PatchSanitizerError(error_message)

        stream_input = io.StringIO(self.raw_patch_content)
        with self.assertRaises(PatchPipelineError) as ctx:
            execute_patch_pipeline(self.repo_path, stream_input, backup_tag=self.backup_tag)

        self.assertIn("Sanitization failed", str(ctx.exception))
        self.assertIn(error_message, str(ctx.exception))

    @patch("skills.patch_pipeline_executor.PatchSanitizer")
    def test_execute_patch_pipeline_unexpected_sanitization_error(self, mock_sanitizer_cls):
        error_message = f"Unexpected error {uuid.uuid4().hex}"
        mock_sanitizer = mock_sanitizer_cls.return_value
        mock_sanitizer.sanitize.side_effect = RuntimeError(error_message)

        stream_input = io.StringIO(self.raw_patch_content)
        with self.assertRaises(PatchPipelineError) as ctx:
            execute_patch_pipeline(self.repo_path, stream_input)

        self.assertIn("Unexpected sanitization error", str(ctx.exception))
        self.assertIn(error_message, str(ctx.exception))

    @patch("skills.patch_pipeline_executor.PatchApplier")
    @patch("skills.patch_pipeline_executor.PatchSanitizer")
    def test_execute_patch_pipeline_recovery_point_error(self, mock_sanitizer_cls, mock_applier_cls):
        mock_sanitizer = mock_sanitizer_cls.return_value
        mock_sanitizer.sanitize.return_value = self.sanitized_patch_content

        error_message = f"Recovery point failure {uuid.uuid4().hex}"
        mock_applier = mock_applier_cls.return_value
        mock_applier.create_recovery_point.side_effect = Exception(error_message)

        stream_input = io.StringIO(self.raw_patch_content)
        with self.assertRaises(PatchPipelineError) as ctx:
            execute_patch_pipeline(self.repo_path, stream_input, backup_tag=self.backup_tag)

        self.assertIn("Failed to create recovery point", str(ctx.exception))
        self.assertIn(error_message, str(ctx.exception))

    @patch("skills.patch_pipeline_executor.PatchApplier")
    @patch("skills.patch_pipeline_executor.PatchSanitizer")
    def test_execute_patch_pipeline_application_error(self, mock_sanitizer_cls, mock_applier_cls):
        mock_sanitizer = mock_sanitizer_cls.return_value
        mock_sanitizer.sanitize.return_value = self.sanitized_patch_content

        error_message = f"Application failed {uuid.uuid4().hex}"
        mock_applier = mock_applier_cls.return_value
        mock_applier.apply_patch.side_effect = PatchApplierError(error_message)

        stream_input = io.StringIO(self.raw_patch_content)
        with self.assertRaises(PatchPipelineError) as ctx:
            execute_patch_pipeline(self.repo_path, stream_input, backup_tag=self.backup_tag)

        self.assertIn("Application failed", str(ctx.exception))
        self.assertIn(error_message, str(ctx.exception))

    @patch("skills.patch_pipeline_executor.PatchApplier")
    @patch("skills.patch_pipeline_executor.PatchSanitizer")
    def test_execute_patch_pipeline_unexpected_application_error(self, mock_sanitizer_cls, mock_applier_cls):
        mock_sanitizer = mock_sanitizer_cls.return_value
        mock_sanitizer.sanitize.return_value = self.sanitized_patch_content

        error_message = f"Unexpected app error {uuid.uuid4().hex}"
        mock_applier = mock_applier_cls.return_value
        mock_applier.apply_patch.side_effect = KeyError(error_message)

        stream_input = io.StringIO(self.raw_patch_content)
        with self.assertRaises(PatchPipelineError) as ctx:
            execute_patch_pipeline(self.repo_path, stream_input)

        self.assertIn("Unexpected application error", str(ctx.exception))
        self.assertIn(error_message, str(ctx.exception))