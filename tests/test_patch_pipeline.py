import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import string

from skills.patch_pipeline import PatchPipeline
from skills.patch_sanitizer import PatchSanitizer
from skills.patch_checker import PatchChecker
from skills.patch_applier import PatchApplier

class TestPatchPipeline(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.pipeline = PatchPipeline(repo_path=self.repo_path)

    def test_pipeline_execution_flow_success(self):
        raw_patch = "".join(random.choices(string.ascii_letters, k=100))
        sanitized_patch = f"sanitized_{raw_patch}"
        check_result = {"status": "ok", "id": uuid.uuid4().hex}

        with patch('skills.patch_pipeline.PatchSanitizer') as MockSanitizer, \
             patch('skills.patch_pipeline.PatchChecker') as MockChecker, \
             patch('skills.patch_pipeline.PatchApplier') as MockApplier:

            instance_sanitizer = MockSanitizer.return_value
            instance_sanitizer.sanitize.return_value = sanitized_patch

            instance_checker = MockChecker.return_value
            instance_checker.check_patch.return_value = check_result

            instance_applier = MockApplier.return_value
            instance_applier.safe_apply.return_value = True

            result = self.pipeline.run(raw_patch)

            self.assertTrue(result)
            instance_sanitizer.sanitize.assert_called_once_with(raw_patch)
            instance_checker.check_patch.assert_called_once_with(sanitized_patch, None)
            instance_applier.safe_apply.assert_called_once()

    def test_pipeline_fails_on_sanitization_error(self):
        raw_patch = uuid.uuid4().hex

        with patch('skills.patch_pipeline.PatchSanitizer') as MockSanitizer:
            instance = MockSanitizer.return_value
            instance.sanitize.side_effect = Exception("Sanitization failed")

            with self.assertRaises(Exception) as cm:
                self.pipeline.run(raw_patch)
            self.assertEqual(str(cm.exception), "Sanitization failed")

    def test_pipeline_fails_on_check_rejection(self):
        raw_patch = uuid.uuid4().hex
        rejection_id = uuid.uuid4().hex

        with patch('skills.patch_pipeline.PatchSanitizer') as MockSanitizer, \
             patch('skills.patch_pipeline.PatchChecker') as MockChecker:

            MockSanitizer.return_value.sanitize.return_value = raw_patch
            MockChecker.return_value.check_patch.return_value = {"status": "rejected", "reason": rejection_id}

            result = self.pipeline.run(raw_patch)

            self.assertFalse(result)

    def test_pipeline_applier_rollback_on_failure(self):
        raw_patch = uuid.uuid4().hex
        backup_tag = uuid.uuid4().hex

        with patch('skills.patch_pipeline.PatchSanitizer') as MockSanitizer, \
             patch('skills.patch_pipeline.PatchChecker') as MockChecker, \
             patch('skills.patch_pipeline.PatchApplier') as MockApplier:

            MockSanitizer.return_value.sanitize.return_value = raw_patch
            MockChecker.return_value.check_patch.return_value = {"status": "ok"}

            applier_instance = MockApplier.return_value
            applier_instance.safe_apply.return_value = False

            result = self.pipeline.run(raw_patch, backup_tag=backup_tag)

            self.assertFalse(result)
            applier_instance.rollback.assert_called_once_with(backup_tag)

    def test_pipeline_stream_handling(self):
        random_bytes = bytes(random.getrandbits(8) for _ in range(64))
        stream = io.BytesIO(random_bytes)

        with patch('skills.patch_pipeline.PatchSanitizer') as MockSanitizer, \
             patch('skills.patch_pipeline.PatchApplier') as MockApplier:
            instance = MockSanitizer.return_value
            instance.sanitize.return_value = "processed_stream"

            self.pipeline.run_from_stream(stream)

            instance.sanitize.assert_called_once()
            args, _ = instance.sanitize.call_args
            self.assertEqual(args[0], stream)

if __name__ == '__main__':
    unittest.main()