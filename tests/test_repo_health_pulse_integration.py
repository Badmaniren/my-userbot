import unittest
import uuid
import random
import tempfile
import pathlib
import os

from skills.repo_health_pulse import repo_health_pulse
from skills.repo_analytics import repo_analytics
from skills.repo_auditor import repo_auditor
from skills.repo_monitor import repo_monitor
from skills.repo_logger import repo_logger

class TestRepoHealthPulseIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.unique_run_id = str(uuid.uuid4())
        self.metric_threshold = random.randint(10, 100)

        os.makedirs(os.path.join(self.repo_path, ".git"), exist_ok=True)
        self.dummy_file = pathlib.Path(self.repo_path) / f"code_{uuid.uuid4()}.py"
        self.dummy_file.write_text(f"# Test file {self.unique_run_id}\nprint('health pulse')\n")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_repo_health_pulse_real_integration(self):
        monitor_result = repo_monitor(repo_path=self.repo_path, run_id=self.unique_run_id)
        self.assertIsNotNone(monitor_result)

        audit_data = repo_auditor(path=self.repo_path, threshold=self.metric_threshold)
        self.assertIsInstance(audit_data, dict)

        analytics_output = repo_analytics(metrics=audit_data, run_id=self.unique_run_id)
        self.assertIsNotNone(analytics_output)

        pulse_output = repo_health_pulse(
            repo_path=self.repo_path,
            analytics=analytics_output,
            run_id=self.unique_run_id
        )

        self.assertIsInstance(pulse_output, dict)
        self.assertIn("status", pulse_output)
        self.assertEqual(pulse_output.get("run_id"), self.unique_run_id)

        log_check = repo_logger(run_id=self.unique_run_id)
        self.assertTrue(log_check or pulse_output.get("status") in ["healthy", "degraded", "critical"])

        report_file_path = pathlib.Path(self.repo_path) / f"health_report_{self.unique_run_id}.json"
        self.assertTrue(report_file_path.exists(), "Интеграционный тест требует реального создания файла отчета модулем pulse")
        
        file_content = report_file_path.read_text()
        self.assertIn(self.unique_run_id, file_content)

if __name__ == "__main__":
    unittest.main()