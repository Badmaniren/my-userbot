import io
import random
import string
import unittest
from unittest.mock import patch, MagicMock
import uuid

from skills.repo_health_automator import RepoHealthAutomator


class TestRepoHealthAutomator(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex[:8]}"

    def test_init_and_public_signatures(self):
        rand_diagnostic_res = {uuid.uuid4().hex: random.randint(1, 100)}
        rand_restorer_res = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.repo_health_automator.RepoHealthDiagnostic") as mock_diag_cls, \
             patch("skills.repo_health_automator.RepoHealthRestorer") as mock_rest_cls:
            
            mock_diag_instance = mock_diag_cls.return_value
            mock_diag_instance.run_full_diagnostic.return_value = rand_diagnostic_res

            mock_rest_instance = mock_rest_cls.return_value
            mock_rest_instance.restore_and_protect.return_value = rand_restorer_res

            automator = RepoHealthAutomator(self.repo_path)
            
            mock_diag_cls.assert_called_once_with(self.repo_path)
            mock_rest_cls.assert_called_once_with(self.repo_path)

            res = automator.automate_health_and_maintenance()

            mock_diag_instance.run_full_diagnostic.assert_called_once_with(self.repo_path)
            mock_rest_instance.restore_and_protect.assert_called_once()

            self.assertEqual(res["monitor_status"], rand_diagnostic_res)
            self.assertEqual(res["health_audit"], rand_restorer_res)
            self.assertIn("preventive_maintenance", res)

    def test_process_stream_and_automate(self):
        stream_content = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        stream = io.StringIO(stream_content)

        rand_diag_key = uuid.uuid4().hex
        rand_diag_val = random.randint(100, 999)
        rand_rest_key = uuid.uuid4().hex
        rand_rest_val = uuid.uuid4().hex

        with patch("skills.repo_health_automator.RepoHealthDiagnostic") as mock_diag_cls, \
             patch("skills.repo_health_automator.RepoHealthRestorer") as mock_rest_cls:

            mock_diag_instance = mock_diag_cls.return_value
            mock_diag_instance.run_full_diagnostic.return_value = {rand_diag_key: rand_diag_val}

            mock_rest_instance = mock_rest_cls.return_value
            mock_rest_instance.comprehensive_health_restoration.return_value = {rand_rest_key: rand_rest_val}

            automator = RepoHealthAutomator(self.repo_path)
            result = automator.process_stream_and_automate(stream)

            mock_diag_instance.run_full_diagnostic.assert_called_once_with(self.repo_path)
            mock_rest_instance.comprehensive_health_restoration.assert_called_once()

            self.assertEqual(result["monitor_status"][rand_diag_key], rand_diag_val)
            self.assertEqual(result["health_audit"][rand_rest_key], rand_rest_val)

    def test_run_alias(self):
        rand_val = uuid.uuid4().hex
        with patch("skills.repo_health_automator.RepoHealthDiagnostic") as mock_diag_cls, \
             patch("skills.repo_health_automator.RepoHealthRestorer") as mock_rest_cls:

            mock_diag_instance = mock_diag_cls.return_value
            mock_diag_instance.run_full_diagnostic.return_value = {"val": rand_val}

            mock_rest_instance = mock_rest_cls.return_value
            mock_rest_instance.restore_and_protect.return_value = {"status": "ok"}

            automator = RepoHealthAutomator(self.repo_path)
            result = automator.run()

            self.assertEqual(result["monitor_status"]["val"], rand_val)

    def test_automate_health_check_alias(self):
        rand_val = random.randint(1000, 9999)
        with patch("skills.repo_health_automator.RepoHealthDiagnostic") as mock_diag_cls, \
             patch("skills.repo_health_automator.RepoHealthRestorer") as mock_rest_cls:

            mock_diag_instance = mock_diag_cls.return_value
            mock_diag_instance.run_full_diagnostic.return_value = {"metric": rand_val}

            mock_rest_instance = mock_rest_cls.return_value
            mock_rest_instance.restore_and_protect.return_value = {"restored": True}

            automator = RepoHealthAutomator(self.repo_path)
            result = automator.automate_health_check()

            self.assertEqual(result["monitor_status"]["metric"], rand_val)


if __name__ == "__main__":
    unittest.main()