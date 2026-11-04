import unittest
from unittest.mock import patch
import uuid
import random
import io
import string

from skills.repo_health_automator import RepoHealthAutomator

class TestRepoHealthAutomator(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.automator = RepoHealthAutomator(self.repo_path)

    def test_init_sets_repo_path(self):
        self.assertEqual(self.automator.repo_path, self.repo_path)

    def test_composition_calls_mandatory_skills(self):
        expected_status = f"status_{uuid.uuid4().hex}"
        expected_health = {
            f"metric_{uuid.uuid4().hex}": random.randint(1, 100),
            f"status_{uuid.uuid4().hex}": uuid.uuid4().hex
        }
        expected_maintenance = {
            f"action_{uuid.uuid4().hex}": ''.join(random.choices(string.ascii_letters, k=10))
        }

        with patch('skills.repo_monitor.RepoMonitor.check_status') as mock_check_status, \
             patch('skills.repo_health_guardian.RepoHealthGuardian.check_health_and_audit') as mock_check_health, \
             patch('skills.repo_health_guardian.RepoHealthGuardian.run_preventive_maintenance') as mock_maintenance:

            mock_check_status.return_value = expected_status
            mock_check_health.return_value = expected_health
            mock_maintenance.return_value = expected_maintenance

            result = self.automator.automate_health_and_maintenance()

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("monitor_status"), expected_status)
            self.assertEqual(result.get("health_audit"), expected_health)
            self.assertEqual(result.get("preventive_maintenance"), expected_maintenance)

            mock_check_status.assert_called_once()
            mock_check_health.assert_called_once()
            mock_maintenance.assert_called_once()

    def test_process_stream_with_composition(self):
        stream_data = f"stream_payload_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(stream_data)

        expected_status = f"status_stream_{uuid.uuid4().hex}"
        expected_health = {
            f"stream_metric_{uuid.uuid4().hex}": random.randint(100, 999)
        }

        with patch('skills.repo_monitor.RepoMonitor.check_status') as mock_check_status, \
             patch('skills.repo_health_guardian.RepoHealthGuardian.check_health_and_audit') as mock_check_health, \
             patch('skills.repo_health_guardian.RepoHealthGuardian.run_preventive_maintenance') as mock_maintenance:

            mock_check_status.return_value = expected_status
            mock_check_health.return_value = expected_health
            mock_maintenance.return_value = {f"fixed_{uuid.uuid4().hex}": True}

            result = self.automator.process_stream_and_automate(stream)

            self.assertEqual(result["monitor_status"], expected_status)
            self.assertEqual(result["health_audit"], expected_health)
            self.assertIn("preventive_maintenance", result)

if __name__ == '__main__':
    unittest.main()