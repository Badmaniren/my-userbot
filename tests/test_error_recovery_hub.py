import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

from skills.error_recovery_hub import ErrorRecoveryHub


class TestErrorRecoveryHub(unittest.TestCase):

    def setUp(self):
        self.hub = ErrorRecoveryHub()
        self.random_module_name = f"mod_{uuid.uuid4().hex[:8]}"
        self.random_error_msg = f"err_{uuid.uuid4().hex}"
        self.random_traceback = f"Traceback (most recent call last):\n  File \"/{uuid.uuid4().hex}.py\", line {random.randint(1, 100)}, in <module>\n    raise Exception('{self.random_error_msg}')"
        self.random_patch_id = uuid.uuid4().hex

    def test_capture_failure_and_logging(self):
        with patch('skills.error_recovery_hub.datetime') as mock_datetime:
            mock_now = MagicMock()
            mock_now.isoformat.return_value = uuid.uuid4().hex
            mock_datetime.now.return_value = mock_now

            incident_id = self.hub.capture_failure(
                module_name=self.random_module_name,
                exception=RuntimeError(self.random_error_msg),
                traceback_str=self.random_traceback
            )

            self.assertIsInstance(incident_id, str)
            self.assertTrue(len(incident_id) > 0)
            
            history = self.hub.get_incident_history(self.random_module_name)
            self.assertIsInstance(history, list)
            self.assertTrue(any(inc.get('error') == self.random_error_msg for inc in history))

    def test_analyze_failure_pattern(self):
        exception_types = [ValueError, TypeError, KeyError, ZeroDivisionError]
        chosen_exception = random.choice(exception_types)(self.random_error_msg)

        incident_id = self.hub.capture_failure(
            module_name=self.random_module_name,
            exception=chosen_exception,
            traceback_str=self.random_traceback
        )

        analysis = self.hub.analyze_failure(incident_id)
        
        self.assertIsInstance(analysis, dict)
        self.assertIn('root_cause', analysis)
        self.assertIn('severity', analysis)
        self.assertEqual(analysis.get('exception_type'), type(chosen_exception).__name__)

    @patch('skills.error_recovery_hub.requests.post')
    def test_automatic_patch_generation(self, mock_requests_post):
        expected_patch_payload = {
            "patch_id": self.random_patch_id,
            "code": f"def fix_{uuid.uuid4().hex[:6]}(): pass"
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = expected_patch_payload
        mock_requests_post.return_value = mock_response

        incident_id = self.hub.capture_failure(
            module_name=self.random_module_name,
            exception=AttributeError(self.random_error_msg),
            traceback_str=self.random_traceback
        )

        patch_result = self.hub.generate_patch(incident_id)

        self.assertIsInstance(patch_result, dict)
        self.assertEqual(patch_result.get('patch_id'), self.random_patch_id)
        self.assertIn('code', patch_result)
        mock_requests_post.assert_called_once()

    def test_apply_patch_to_module(self):
        random_file_content = f"# {uuid.uuid4().hex}\noriginal_variable = {random.randint(100, 999)}\n"
        mock_file_data = io.BytesIO(random_file_content.encode('utf-8'))

        with patch('skills.error_recovery_hub.open', create=True) as mock_open:
            mock_file_instance = MagicMock()
            mock_file_instance.read.return_value = random_file_content
            mock_open.return_value.__enter__.return_value = mock_file_instance

            patch_data = {
                "patch_id": self.random_patch_id,
                "target_module": self.random_module_name,
                "replacement": f"original_variable = {random.randint(1000, 9999)}"
            }

            success = self.hub.apply_patch(patch_data)
            self.assertTrue(success)
            mock_open.assert_called()
            mock_file_instance.write.assert_called()

    def test_recovery_hub_rollback_on_failure(self):
        random_backup_data = f"backup_state_{uuid.uuid4().hex}"
        
        incident_id = self.hub.capture_failure(
            module_name=self.random_module_name,
            exception=SystemError(self.random_error_msg),
            traceback_str=self.random_traceback
        )

        with patch.object(self.hub, '_execute_patch', side_effect=Exception(f"Failed to apply: {uuid.uuid4().hex}")):
            with patch.object(self.hub, '_restore_backup') as mock_restore:
                patch_payload = {
                    "patch_id": self.random_patch_id,
                    "target_module": self.random_module_name
                }
                
                result = self.hub.deploy_and_verify(incident_id, patch_payload)
                
                self.assertFalse(result)
                mock_restore.assert_called_once()

    def test_invalid_incident_handling(self):
        fake_incident_id = f"nonexistent_{uuid.uuid4().hex}"
        
        analysis = self.hub.analyze_failure(fake_incident_id)
        self.assertIsInstance(analysis, dict)
        self.assertTrue(analysis.get('error') or analysis.get('status') == 'not_found')

        patch_res = self.hub.generate_patch(fake_incident_id)
        self.assertIsInstance(patch_res, dict)
        self.assertTrue(patch_res.get('error') or patch_res.get('status') == 'not_found')


if __name__ == '__main__':
    unittest.main()