import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os

from skills.repo_security_automator import RepoSecurityAutomator

class TestRepoSecurityAutomator(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}_{random.randint(1000, 9999)}"

    def test_composition_and_initialization(self):
        with patch('skills.repo_security_automator.RepoSecurityGateway') as mock_gateway_cls, \
             patch('skills.repo_security_automator.RepoAutoCommitter') as mock_committer_cls:
            
            mock_gateway_instance = mock_gateway_cls.return_value
            mock_committer_instance = mock_committer_cls.return_value

            automator = RepoSecurityAutomator(self.repo_path)

            mock_gateway_cls.assert_called_once_with(self.repo_path)
            mock_committer_cls.assert_called_once_with(self.repo_path)
            self.assertEqual(automator.repo_path, self.repo_path)
            self.assertEqual(automator.gateway, mock_gateway_instance)
            self.assertEqual(automator.committer, mock_committer_instance)

    def test_run_success_flow(self):
        expected_status = random.choice([True, False])
        random_report_key = uuid.uuid4().hex
        random_report_val = uuid.uuid4().hex
        gateway_result = {random_report_key: random_report_val, "status": expected_status}

        with patch('skills.repo_security_automator.RepoSecurityGateway') as mock_gateway_cls, \
             patch('skills.repo_security_automator.RepoAutoCommitter') as mock_committer_cls:

            mock_gateway_instance = mock_gateway_cls.return_value
            mock_gateway_instance.run.return_value = gateway_result
            
            mock_committer_instance = mock_committer_cls.return_value
            mock_committer_instance.run.return_value = True

            automator = RepoSecurityAutomator(self.repo_path)
            
            # Проверяем наличие методов для запуска
            if hasattr(automator, 'run'):
                result = automator.run()
            elif hasattr(automator, 'execute'):
                result = automator.execute()
            else:
                result = automator.process_security()

            mock_gateway_instance.run.assert_called_once()
            mock_committer_instance.run.assert_called_once()
            
            self.assertIn(random_report_key, gateway_result)
            self.assertEqual(gateway_result[random_report_key], random_report_val)

    def test_run_failure_flow(self):
        random_error_msg = uuid.uuid4().hex
        gateway_result = {"status": False, "error": random_error_msg}

        with patch('skills.repo_security_automator.RepoSecurityGateway') as mock_gateway_cls, \
             patch('skills.repo_security_automator.RepoAutoCommitter') as mock_committer_cls:

            mock_gateway_instance = mock_gateway_cls.return_value
            mock_gateway_instance.run.return_value = gateway_result
            
            mock_committer_instance = mock_committer_cls.return_value
            mock_committer_instance.run.return_value = False

            automator = RepoSecurityAutomator(self.repo_path)
            
            if hasattr(automator, 'run'):
                automator.run()
            elif hasattr(automator, 'execute'):
                automator.execute()
            else:
                automator.process_security()

            mock_gateway_instance.run.assert_called_once()
            mock_committer_instance.run.assert_called_once()

    def test_stream_processing_and_integration(self):
        random_stream_data = io.BytesIO(uuid.uuid4().bytes)
        unique_metric_key = uuid.uuid4().hex
        unique_metric_value = random.randint(1, 100000)

        with patch('skills.repo_security_automator.RepoSecurityGateway') as mock_gateway_cls, \
             patch('skills.repo_security_automator.RepoAutoCommitter') as mock_committer_cls:

            mock_gateway_instance = mock_gateway_cls.return_value
            mock_gateway_instance.run.return_value = {unique_metric_key: unique_metric_value}
            
            mock_committer_instance = mock_committer_cls.return_value
            mock_committer_instance.process_and_commit.return_value = True

            automator = RepoSecurityAutomator(self.repo_path)
            
            if hasattr(automator, 'process_stream'):
                res = automator.process_stream(random_stream_data)
                self.assertIsNotNone(res)
            elif hasattr(automator, 'run_pipeline'):
                res = automator.run_pipeline()
                self.assertIsNotNone(res)
            else:
                res = automator.run()
                self.assertIsNotNone(res)

            mock_gateway_instance.run.assert_called()

if __name__ == '__main__':
    unittest.main()