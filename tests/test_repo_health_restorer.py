import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
import uuid
import random
import string

from skills.repo_health_restorer import RepoHealthRestorer


class TestRepoHealthRestorer(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.restorer = RepoHealthRestorer(self.repo_path)

    def test_init_sets_paths_and_components(self):
        self.assertEqual(self.restorer.repo_path, self.repo_path)
        self.assertIsNotNone(self.restorer.guardian)
        self.assertIsNotNone(self.restorer.recovery)

    @patch("skills.repo_health_guardian.RepoHealthGuardian.run_preventive_maintenance")
    @patch("skills.repo_recovery.RepoRecovery.recover_repository")
    def test_restore_and_protect(self, mock_recover, mock_maintenance):
        rand_status = random.choice([True, False])
        rand_report_key = uuid.uuid4().hex
        rand_report_val = uuid.uuid4().hex

        mock_recover.return_value = rand_status
        mock_maintenance.return_value = {rand_report_key: rand_report_val}

        result = self.restorer.restore_and_protect()

        self.assertIsInstance(result, dict)
        self.assertIn("recovery_status", result)
        self.assertIn("maintenance_report", result)
        self.assertEqual(result["recovery_status"], rand_status)
        self.assertEqual(result["maintenance_report"], {rand_report_key: rand_report_val})

        mock_maintenance.assert_called_once()
        mock_recover.assert_called_once()

    @patch("skills.repo_health_guardian.RepoHealthGuardian.analyze_repo_structure")
    @patch("skills.repo_recovery.RepoRecovery.safe_restore")
    def test_comprehensive_health_restoration_with_string(self, mock_safe_restore, mock_analyze):
        rand_analysis_key = uuid.uuid4().hex
        rand_analysis_val = uuid.uuid4().hex
        rand_restored = random.choice([True, False])
        input_string = "".join(random.choices(string.ascii_letters, k=16))

        mock_analyze.return_value = {rand_analysis_key: rand_analysis_val}
        mock_safe_restore.return_value = rand_restored

        result = self.restorer.comprehensive_health_restoration(input_string)

        self.assertIsInstance(result, dict)
        self.assertIn("restored", result)
        self.assertIn("structure_analysis", result)
        self.assertEqual(result["restored"], rand_restored)
        self.assertEqual(result["structure_analysis"], {rand_analysis_key: rand_analysis_val})

        mock_analyze.assert_called_once()
        mock_safe_restore.assert_called_once()
        
        args, _ = mock_safe_restore.call_args
        passed_stream = args[0]
        self.assertIsInstance(passed_stream, BytesIO)
        self.assertEqual(passed_stream.read().decode("utf-8"), input_string)

    @patch("skills.repo_health_guardian.RepoHealthGuardian.analyze_repo_structure")
    @patch("skills.repo_recovery.RepoRecovery.safe_restore")
    def test_comprehensive_health_restoration_with_bytesio(self, mock_safe_restore, mock_analyze):
        rand_analysis_key = uuid.uuid4().hex
        rand_analysis_val = uuid.uuid4().hex
        rand_restored = random.choice([True, False])
        stream_data = BytesIO(uuid.uuid4().hex.encode("utf-8"))

        mock_analyze.return_value = {rand_analysis_key: rand_analysis_val}
        mock_safe_restore.return_value = rand_restored

        result = self.restorer.comprehensive_health_restoration(stream_data)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["restored"], rand_restored)
        self.assertEqual(result["structure_analysis"], {rand_analysis_key: rand_analysis_val})

        mock_safe_restore.assert_called_once_with(stream_data)

    @patch("skills.repo_health_guardian.RepoHealthGuardian.check_health_and_audit")
    @patch("skills.repo_recovery.RepoRecovery.recover_repository")
    def test_execute_restoration_routine(self, mock_recover, mock_audit):
        rand_status = random.choice([True, False])
        mock_recover.return_value = rand_status

        status = self.restorer.execute_restoration_routine()

        self.assertEqual(status, rand_status)
        mock_audit.assert_called_once()
        mock_recover.assert_called_once()


if __name__ == "__main__":
    unittest.main()