import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import string

from skills.patch_pipeline_controller import PatchPipelineController

class TestPatchPipelineController(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.controller = PatchPipelineController(repo_path=self.repo_path)

    def test_pipeline_execution_flow_success(self):
        raw_patch = "".join(random.choices(string.ascii_letters, k=128))
        sanitized_patch = f"CLEAN_{raw_patch}"
        check_result = {"status": "valid", "score": random.random()}

        with patch('skills.patch_pipeline_controller.patch_sanitizer.PatchSanitizer') as mock_sanitizer, \
             patch('skills.patch_pipeline_controller.patch_checker.PatchChecker') as mock_checker, \
             patch('skills.patch_pipeline_controller.patch_applier.PatchApplier') as mock_applier:

            instance_sanitizer = mock_sanitizer.return_value
            instance_sanitizer.sanitize.return_value = sanitized_patch

            instance_checker = mock_checker.return_value
            instance_checker.check_patch.return_value = check_result

            instance_applier = mock_applier.return_value
            instance_applier.apply_patch.return_value = True

            result = self.controller.process(raw_patch)

            self.assertTrue(result)
            instance_sanitizer.sanitize.assert_called_once_with(raw_patch)
            instance_checker.check_patch.assert_called_once()
            instance_applier.apply_patch.assert_called_once_with(sanitized_patch)

    def test_pipeline_fails_on_sanitization_error(self):
        raw_patch = uuid.uuid4().hex

        with patch('skills.patch_pipeline_controller.patch_sanitizer.PatchSanitizer') as mock_sanitizer:
            instance_sanitizer = mock_sanitizer.return_value
            instance_sanitizer.sanitize.side_effect = Exception("Sanitization failed")

            with self.assertRaises(Exception):
                self.controller.process(raw_patch)

    def test_pipeline_aborts_on_invalid_check(self):
        raw_patch = uuid.uuid4().hex
        check_result = {"status": "invalid", "reason": uuid.uuid4().hex}

        with patch('skills.patch_pipeline_controller.patch_sanitizer.PatchSanitizer') as mock_sanitizer, \
             patch('skills.patch_pipeline_controller.patch_checker.PatchChecker') as mock_checker:

            mock_sanitizer.return_value.sanitize.return_value = raw_patch
            mock_checker.return_value.check_patch.return_value = check_result

            result = self.controller.process(raw_patch)

            self.assertFalse(result)

    def test_pipeline_rollback_on_apply_failure(self):
        raw_patch = uuid.uuid4().hex
        backup_tag = uuid.uuid4().hex

        with patch('skills.patch_pipeline_controller.patch_sanitizer.PatchSanitizer') as mock_sanitizer, \
             patch('skills.patch_pipeline_controller.patch_checker.PatchChecker') as mock_checker, \
             patch('skills.patch_pipeline_controller.patch_applier.PatchApplier') as mock_applier:

            mock_sanitizer.return_value.sanitize.return_value = raw_patch
            mock_checker.return_value.check_patch.return_value = {"status": "valid"}

            instance_applier = mock_applier.return_value
            instance_applier.apply_patch.return_value = False

            result = self.controller.process(raw_patch, backup_tag=backup_tag)

            self.assertFalse(result)
            instance_applier.rollback.assert_called_once_with(backup_tag)

    def test_data_integrity_in_pipeline(self):
        random_data = io.BytesIO(uuid.uuid4().bytes)
        expected_output = uuid.uuid4().hex

        with patch('skills.patch_pipeline_controller.patch_sanitizer.PatchSanitizer') as mock_sanitizer:
            mock_sanitizer.return_value.sanitize.return_value = expected_output

            result = self.controller.sanitize_stream(random_data)

            self.assertEqual(result, expected_output)
            mock_sanitizer.return_value.sanitize.assert_called_with(random_data)

if __name__ == '__main__':
    unittest.main()