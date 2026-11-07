import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
import random
import uuid
import string

from skills.repo_health_restorer import RepoHealthRestorer


class TestRepoHealthRestorer(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.restorer = RepoHealthRestorer(self.repo_path)

    def test_init_sets_attributes(self):
        random_path = f"/var/repo/{uuid.uuid4().hex}"
        restorer = RepoHealthRestorer(random_path)
        self.assertEqual(restorer.repo_path, random_path)
        self.assertIsNotNone(restorer.guardian)
        self.assertIsNotNone(restorer.recovery)

    @patch('skills.repo_health_guardian.RepoHealthGuardian.run_preventive_maintenance')
    @patch('skills.repo_recovery.RepoRecovery.recover_repository')
    def test_restore_and_protect_delegation(self, mock_recover, mock_maintenance):
        expected_maintenance = {
            "status": random.choice(["success", "warning"]),
            "code": random.randint(100, 999),
            "message": uuid.uuid4().hex
        }
        expected_recovery = random.choice([True, False])

        mock_maintenance.return_value = expected_maintenance
        mock_recover.return_value = expected_recovery

        result = self.restorer.restore_and_protect()

        self.assertIsInstance(result, dict)
        self.assertIn("recovery_status", result)
        self.assertIn("maintenance_report", result)
        self.assertEqual(result["recovery_status"], expected_recovery)
        self.assertEqual(result["maintenance_report"], expected_maintenance)
        mock_maintenance.assert_called_once()
        mock_recover.assert_called_once()

    @patch('skills.repo_health_guardian.RepoHealthGuardian.analyze_repo_structure')
    @patch('skills.repo_recovery.RepoRecovery.safe_restore')
    def test_comprehensive_health_restoration_with_string(self, mock_safe_restore, mock_analyze):
        random_stream_str = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        expected_analysis = {
            "node_id": uuid.uuid4().hex,
            "metric": random.random()
        }
        expected_restore_status = random.choice([True, False])

        mock_analyze.return_value = expected_analysis
        mock_safe_restore.return_value = expected_restore_status

        result = self.restorer.comprehensive_health_restoration(random_stream_str)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["restored"], expected_restore_status)
        self.assertEqual(result["structure_analysis"], expected_analysis)
        mock_analyze.assert_called_once()
        mock_safe_restore.assert_called_once()

        passed_arg = mock_safe_restore.call_args[0][0]
        self.assertIsInstance(passed_arg, BytesIO)
        self.assertEqual(passed_arg.read(), random_stream_str.encode("utf-8"))

    @patch('skills.repo_health_guardian.RepoHealthGuardian.analyze_repo_structure')
    @patch('skills.repo_recovery.RepoRecovery.safe_restore')
    def test_comprehensive_health_restoration_with_bytesio(self, mock_safe_restore, mock_analyze):
        random_bytes = uuid.uuid4().hex.encode("utf-8")
        stream = BytesIO(random_bytes)
        expected_analysis = {
            "audit_key": uuid.uuid4().hex,
            "score": random.randint(1, 100)
        }
        expected_restore_status = random.choice([True, False])

        mock_analyze.return_value = expected_analysis
        mock_safe_restore.return_value = expected_restore_status

        result = self.restorer.comprehensive_health_restoration(stream)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["restored"], expected_restore_status)
        self.assertEqual(result["structure_analysis"], expected_analysis)
        mock_analyze.assert_called_once()
        mock_safe_restore.assert_called_once()

        passed_arg = mock_safe_restore.call_args[0][0]
        self.assertEqual(passed_arg, stream)
        self.assertEqual(passed_arg.read(), random_bytes)

    @patch('skills.repo_health_guardian.RepoHealthGuardian.check_health_and_audit')
    @patch('skills.repo_recovery.RepoRecovery.recover_repository')
    def test_execute_restoration_routine(self, mock_recover, mock_audit):
        expected_status = random.choice([True, False])
        mock_recover.return_value = expected_status

        result = self.restorer.execute_restoration_routine()

        self.assertEqual(result, expected_status)
        mock_audit.assert_called_once()
        mock_recover.assert_called_once()


if __name__ == '__main__':
    unittest.main()