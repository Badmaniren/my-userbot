import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
import os

from skills.patch_validator import PatchValidator, PatchValidatorError

class TestPatchValidator(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.validator = PatchValidator(repo_path=self.repo_path)

    def _generate_random_patch(self):
        return f"--- a/{uuid.uuid4().hex}\n+++ b/{uuid.uuid4().hex}\n@@ -1,1 +1,1 @@\n-{uuid.uuid4().hex}\n+{uuid.uuid4().hex}"

    def test_validate_integrity_success(self):
        patch_content = self._generate_random_patch()
        expected_id = uuid.uuid4().hex

        with patch('skills.patch_validator.GitInspector') as mock_git:
            instance = mock_git.return_value
            instance.get_file_diff.return_value = patch_content

            result = self.validator.validate_integrity(expected_id)
            self.assertTrue(result)
            instance.get_file_diff.assert_called_with(expected_id)

    def test_validate_security_raises_error_on_malicious_content(self):
        malicious_payload = f"rm -rf / && {uuid.uuid4().hex}"

        with patch('skills.patch_validator.CodeSanitizer') as mock_sanitizer:
            mock_sanitizer.return_value.check.side_effect = Exception("Security Violation")

            with self.assertRaises(PatchValidatorError):
                self.validator.validate_security(malicious_payload)

    def test_apply_validation_pipeline_integration(self):
        patch_data = self._generate_random_patch()
        mock_id = uuid.uuid4().hex

        with patch('skills.patch_validator.PatchSanitizer') as mock_sanitizer, \
             patch('skills.patch_validator.PatchChecker') as mock_checker:

            mock_sanitizer.return_value.sanitize.return_value = patch_data
            mock_checker.return_value.check.return_value = True

            status = self.validator.run_validation_pipeline(patch_data, mock_id)

            self.assertTrue(status)
            mock_sanitizer.return_value.sanitize.assert_called_once()
            mock_checker.return_value.check.assert_called_with(patch_data)

    def test_telemetry_logging_on_failure(self):
        random_error_msg = ''.join(random.choices(string.ascii_letters, k=20))

        with patch('skills.patch_validator.AnomalyLogger') as mock_logger:
            logger_instance = mock_logger.return_value

            try:
                self.validator.validate_integrity(None)
            except Exception:
                pass

            self.assertTrue(logger_instance.log_anomaly.called)
            args, _ = logger_instance.log_anomaly.call_args
            self.assertIn("integrity", args[0])

    def test_patch_size_constraint(self):
        large_patch = "a" * 1024 * 1024

        with self.assertRaises(PatchValidatorError):
            self.validator.validate_integrity(large_patch)

    def test_file_stream_processing(self):
        random_bytes = os.urandom(64)
        mock_file = io.BytesIO(random_bytes)

        with patch('builtins.open', return_value=mock_file):
            result = self.validator.process_patch_file(f"{uuid.uuid4().hex}.patch")
            self.assertIsNotNone(result)
            self.assertEqual(result, random_bytes.decode('utf-8', errors='ignore'))

    def test_validator_initialization_parameters(self):
        new_repo = f"/var/lib/{uuid.uuid4().hex}"
        validator = PatchValidator(repo_path=new_repo)
        self.assertEqual(validator.repo_path, new_repo)

    def test_anomaly_dispatch_on_critical_failure(self):
        with patch('skills.patch_validator.AnomalyAlertDispatcher') as mock_dispatcher:
            dispatcher_instance = mock_dispatcher.return_value

            with self.assertRaises(PatchValidatorError):
                self.validator.force_fail(uuid.uuid4().hex)

            self.assertTrue(dispatcher_instance.dispatch.called)

if __name__ == '__main__':
    unittest.main()