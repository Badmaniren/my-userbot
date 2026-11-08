import unittest
import uuid
import random
import os
import tempfile
import shutil

from skills.repo_health_pulse_engine import RepoHealthPulseEngine
from skills.repo_monitor import RepoMonitor
from skills.repo_logger import RepoLogger
from skills.repo_analytics import RepoAnalytics

class TestRepoHealthPulseEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.pulse_engine = RepoHealthPulseEngine()
        self.monitor = RepoMonitor()
        self.logger = RepoLogger()
        self.analytics = RepoAnalytics()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pulse_engine_real_integration(self):
        unique_run_id = str(uuid.uuid4())
        metric_value = random.randint(100, 999)
        
        target_file = os.path.join(self.test_dir, f"health_metric_{unique_run_id}.log")
        
        # Вызываем реальные интегрированные навыки без моков
        log_result = self.logger.log_event(target_file, f"RUN_ID:{unique_run_id} VALUE:{metric_value}")
        self.assertTrue(os.path.exists(target_file))

        monitor_status = self.monitor.check_status(self.test_dir)
        self.assertIsInstance(monitor_status, dict)

        pulse_result = self.pulse_engine.collect_and_process_pulse(
            repo_path=self.test_dir,
            run_id=unique_run_id,
            metric=metric_value
        )

        self.assertIn("status", pulse_result)
        self.assertEqual(pulse_result.get("run_id"), unique_run_id)

        analytics_report = self.analytics.generate_metrics_report(self.test_dir)
        self.assertIsInstance(analytics_report, dict)

        with open(target_file, "r") as f:
            content = f.read()
            self.assertIn(unique_run_id, content)
            self.assertIn(str(metric_value), content)

if __name__ == "__main__":
    unittest.main()