import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import string

from skills.patch_pipeline_runner import PatchPipelineRunner
from skills.patch_sanitizer import PatchSanitizerError
from skills.patch_checker import PatchCheckerError
from skills.patch_applier import PatchApplierError

class TestPatchPipelineRunner(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.runner = PatchPipelineRunner(repo_path=self.repo_path)

    def test_pipeline_success_flow(self):
        raw_patch = "".join(random.choices(string.ascii_letters, k=100))
        sanitized_patch = f"clean_{uuid.uuid4().hex}"
        check_result = {"status": "ok", "id": uuid.uuid4().hex}

        with patch('skills.patch_pipeline_runner.PatchSanitizer') as mock_sanitizer, \
             patch('skills.patch_pipeline_runner.PatchChecker') as mock_checker, \
             patch('skills.patch_pipeline_runner.PatchApplier') as mock_applier:

            mock_sanitizer.return_value.sanitize.return_value = sanitized_patch
            mock_checker.return_value.check_patch.return_value = check_result
            mock_applier.return_value.apply_patch.return_value = True

            result = self.runner.run(raw_patch)

            self.assertTrue(result)
            mock_sanitizer.return_value.sanitize.assert_called_once_with(raw_patch)
            mock_checker.return_value.check_patch.assert_called_once()
            mock_applier.return_value.apply_patch.assert_called_once_with(sanitized_patch)

    def test_pipeline_sanitization_failure(self):
        raw_patch = f"bad_data_{uuid.uuid4().hex}"

        with patch('skills.patch_pipeline_runner.PatchSanitizer') as mock_sanitizer:
            mock_sanitizer.return_value.sanitize.side_effect = PatchSanitizerError("Sanitization failed")

            with self.assertRaises(PatchSanitizerError):
                self.runner.run(raw_patch)

    def test_pipeline_checker_rejection(self):
        raw_patch = f"patch_{uuid.uuid4().hex}"

        with patch('skills.patch_pipeline_runner.PatchSanitizer') as mock_sanitizer, \
             patch('skills.patch_pipeline_runner.PatchChecker') as mock_checker:

            mock_sanitizer.return_value.sanitize.return_value = raw_patch
            mock_checker.return_value.check_patch.side_effect = PatchCheckerError("Validation failed")

            with self.assertRaises(PatchCheckerError):
                self.runner.run(raw_patch)

    def test_pipeline_applier_failure_with_rollback(self):
        raw_patch = f"patch_{uuid.uuid4().hex}"
        backup_tag = uuid.uuid4().hex

        with patch('skills.patch_pipeline_runner.PatchSanitizer') as mock_sanitizer, \
             patch('skills.patch_pipeline_runner.PatchChecker') as mock_checker, \
             patch('skills.patch_pipeline_runner.PatchApplier') as mock_applier:

            mock_sanitizer.return_value.sanitize.return_value = raw_patch
            mock_checker.return_value.check_patch.return_value = {"status": "ok"}
            mock_applier.return_value.apply_patch.side_effect = PatchApplierError("Apply failed")

            with self.assertRaises(PatchApplierError):
                self.runner.run(raw_patch)

            mock_applier.return_value.rollback.assert_called()

    def test_stream_processing_integrity(self):
        random_stream = io.BytesIO(uuid.uuid4().bytes)
        expected_output = uuid.uuid4().hex

        with patch('skills.patch_pipeline_runner.PatchSanitizer') as mock_sanitizer, \
             patch('skills.patch_pipeline_runner.PatchChecker') as mock_checker, \
             patch('skills.patch_pipeline_runner.PatchApplier') as mock_applier:

            mock_sanitizer.return_value.sanitize.return_value = expected_output
            mock_checker.return_value.check_patch.return_value = {"status": "ok"}
            mock_applier.return_value.apply_patch.return_value = True

            self.runner.run_from_stream(random_stream)

            mock_sanitizer.return_value.sanitize.assert_called_once()
            args, _ = mock_sanitizer.return_value.sanitize.call_args
            self.assertEqual(args[0], random_stream)

if __name__ == '__main__':
    unittest.main()