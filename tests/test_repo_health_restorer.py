import io
import random
import unittest
import uuid
from unittest.mock import patch, MagicMock

from skills.repo_health_restorer import RepoHealthRestorer


class TestRepoHealthRestorer(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"

    def test_init_sets_repo_path_and_classes(self):
        with patch('skills.repo_health_restorer.RepoHealthGuardian') as mock_guardian_cls, \
             patch('skills.repo_health_restorer.RepoRecovery') as mock_recovery_cls:
            
            restorer = RepoHealthRestorer(self.repo_path)
            
            self.assertEqual(restorer.repo_path, self.repo_path)
            mock_guardian_cls.assert_called_once_with(self.repo_path)
            mock_recovery_cls.assert_called_once_with(self.repo_path)

    def test_restore_and_protect_success(self):
        expected_maintenance = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_recovery = random.choice([True, False])

        with patch('skills.repo_health_restorer.RepoHealthGuardian') as mock_guardian_cls, \
             patch('skills.repo_health_restorer.RepoRecovery') as mock_recovery_cls:
            
            mock_guardian = mock_guardian_cls.return_value
            mock_guardian.run_preventive_maintenance.return_value = expected_maintenance

            mock_recovery = mock_recovery_cls.return_value
            mock_recovery.recover_repository.return_value = expected_recovery

            restorer = RepoHealthRestorer(self.repo_path)
            result = restorer.restore_and_protect()

            mock_guardian.run_preventive_maintenance.assert_called_once()
            mock_recovery.recover_repository.assert_called_once()
            self.assertEqual(result, {
                "recovery_status": expected_recovery,
                "maintenance_report": expected_maintenance,
            })

    def test_comprehensive_health_restoration_stream_handling(self):
        expected_analysis = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_restored = random.choice([True, False])
        random_stream_data = f"stream_data_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(random_stream_data)

        with patch('skills.repo_health_restorer.RepoHealthGuardian') as mock_guardian_cls, \
             patch('skills.repo_health_restorer.RepoRecovery') as mock_recovery_cls:
            
            mock_guardian = mock_guardian_cls.return_value
            mock_guardian.analyze_repo_structure.return_value = expected_analysis

            mock_recovery = mock_recovery_cls.return_value
            mock_recovery.safe_restore.return_value = expected_restored

            restorer = RepoHealthRestorer(self.repo_path)
            result = restorer.comprehensive_health_restoration(stream)

            mock_guardian.analyze_repo_structure.assert_called_once()
            mock_recovery.safe_restore.assert_called_once_with(stream)
            self.assertEqual(result, {
                "restored": expected_restored,
                "structure_analysis": expected_analysis,
            })

    def test_execute_restoration_routine_success_flow(self):
        with patch('skills.repo_health_restorer.RepoHealthGuardian') as mock_guardian_cls, \
             patch('skills.repo_health_restorer.RepoRecovery') as mock_recovery_cls:
            
            mock_guardian = mock_guardian_cls.return_value
            mock_recovery = mock_recovery_cls.return_value
            mock_recovery.recover_repository.return_value = True

            restorer = RepoHealthRestorer(self.repo_path)
            status = restorer.execute_restoration_routine()

            mock_guardian.check_health_and_audit.assert_called_once()
            mock_recovery.recover_repository.assert_called_once()
            self.assertTrue(status)

    def test_execute_restoration_routine_failure_flow(self):
        with patch('skills.repo_health_restorer.RepoHealthGuardian') as mock_guardian_cls, \
             patch('skills.repo_health_restorer.RepoRecovery') as mock_recovery_cls:
            
            mock_guardian = mock_guardian_cls.return_value
            mock_recovery = mock_recovery_cls.return_value
            mock_recovery.recover_repository.return_value = False

            restorer = RepoHealthRestorer(self.repo_path)
            status = restorer.execute_restoration_routine()

            mock_guardian.check_health_and_audit.assert_called_once()
            mock_recovery.recover_repository.assert_called_once()
            self.assertFalse(status)


if __name__ == '__main__':
    unittest.main()