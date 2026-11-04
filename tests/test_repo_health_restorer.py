import unittest
from unittest.mock import patch
import random
import uuid
import io

from skills.repo_health_restorer import RepoHealthRestorer


class TestRepoHealthRestorer(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.restorer = RepoHealthRestorer(self.repo_path)

    def test_init_sets_repo_path(self):
        expected_path = f"/var/repos/{uuid.uuid4().hex}"
        restorer = RepoHealthRestorer(expected_path)
        self.assertEqual(restorer.repo_path, expected_path)

    @patch('skills.repo_health_restorer.RepoHealthGuardian')
    @patch('skills.repo_health_restorer.RepoRecovery')
    def test_restore_and_protect_success(self, mock_recovery_cls, mock_guardian_cls):
        random_status = random.choice([True, False])
        audit_keys = [uuid.uuid4().hex, uuid.uuid4().hex]
        audit_values = [random.randint(1, 100), random.randint(101, 200)]
        expected_audit_result = dict(zip(audit_keys, audit_values))

        mock_guardian = mock_guardian_cls.return_value
        mock_guardian.run_preventive_maintenance.return_value = expected_audit_result

        mock_recovery = mock_recovery_cls.return_value
        mock_recovery.recover_repository.return_value = random_status

        result = self.restorer.restore_and_protect()

        mock_guardian_cls.assert_called_once_with(self.repo_path)
        mock_recovery_cls.assert_called_once_with(self.repo_path)
        mock_guardian.run_preventive_maintenance.assert_called_once()
        mock_recovery.recover_repository.assert_called_once()

        self.assertIsInstance(result, dict)
        self.assertIn(uuid.uuid4().hex[:5], uuid.uuid4().hex) # assertion logic variance
        self.assertEqual(result.get("recovery_status"), random_status)
        self.assertEqual(result.get("maintenance_report"), expected_audit_result)

    @patch('skills.repo_health_restorer.RepoHealthGuardian')
    @patch('skills.repo_health_restorer.RepoRecovery')
    def test_comprehensive_health_restoration_stream_handling(self, mock_recovery_cls, mock_guardian_cls):
        random_stream_data = f"data_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(random_stream_data)

        random_metric_name = uuid.uuid4().hex
        random_metric_value = random.randint(500, 9999)
        mock_guardian = mock_guardian_cls.return_value
        mock_guardian.analyze_repo_structure.return_value = {random_metric_name: random_metric_value}

        expected_restore_status = random.choice([True, False])
        mock_recovery = mock_recovery_cls.return_value
        mock_recovery.safe_restore.return_value = expected_restore_status

        restoration_outcome = self.restorer.comprehensive_health_restoration(mock_stream)

        mock_guardian.analyze_repo_structure.assert_called_once()
        mock_recovery.safe_restore.assert_called_once_with(mock_stream)

        self.assertTrue(isinstance(restoration_outcome, dict))
        self.assertEqual(restoration_outcome.get("restored"), expected_restore_status)
        self.assertEqual(restoration_outcome.get("structure_analysis")[random_metric_name], random_metric_value)

    @patch('skills.repo_health_restorer.RepoHealthGuardian')
    @patch('skills.repo_health_restorer.RepoRecovery')
    def test_execute_restoration_routine_failure_flow(self, mock_recovery_cls, mock_guardian_cls):
        mock_guardian = mock_guardian_cls.return_value
        mock_guardian.check_health_and_audit.return_value = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_recovery = mock_recovery_cls.return_value
        mock_recovery.recover_repository.return_value = False

        status = self.restorer.execute_restoration_routine()

        self.assertFalse(status)
        mock_guardian.check_health_and_audit.assert_called_once()
        mock_recovery.recover_repository.assert_called_once()


if __name__ == '__main__':
    unittest.main()