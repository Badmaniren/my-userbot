import unittest
import uuid
import random
import os
import tempfile

from skills.repo_health_pulse_engine import (
    RepoHealthPulseEngine,
    RepoMonitor,
    RepoLogger,
    RepoAnalytics,
    PulseMetric,
    PulseException
)

class TestRepoHealthPulseEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.engine = RepoHealthPulseEngine()
        self.monitor = RepoMonitor()
        self.logger = RepoLogger()
        self.analytics = RepoAnalytics()
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pulse_engine_integration_workflow(self):
        repo_id = f"repo-{uuid.uuid4()}"
        run_id = f"run-{uuid.uuid4()}"
        repo_path = os.path.join(self.temp_dir.name, f"test_repo_{uuid.uuid4()}")
        os.makedirs(repo_path, exist_ok=True)

        monitor_result = self.monitor.check_status(repo_path)
        self.assertEqual(monitor_result["status"], "ok")
        self.assertEqual(monitor_result["path"], repo_path)

        metric_name = f"security_vuln_{random.randint(100, 999)}"
        pulse_metric = self.engine.collect_metric(repo_id, metric_name)
        self.assertEqual(pulse_metric.repo_id, repo_id)
        self.assertEqual(pulse_metric.name, metric_name)
        self.assertTrue(pulse_metric.is_healthy)

        log_file = os.path.join(repo_path, f"pulse_log_{uuid.uuid4()}.txt")
        log_message = f"INTEGRATION_RUN_{run_id}_METRIC_{metric_name}"
        log_success = self.logger.log_event(log_file, log_message)
        
        self.assertTrue(log_success)
        self.assertTrue(os.path.exists(log_file))

        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        self.assertEqual(content, log_message)

        stream_file = os.path.join(repo_path, f"stream_{uuid.uuid4()}.txt")
        stream_lines = [f"signal_{uuid.uuid4()}" for _ in range(3)]
        with open(stream_file, "w", encoding="utf-8") as f:
            for line in stream_lines:
                f.write(line + "\n")

        monitored_stream = self.engine.monitor_stream(stream_file, limit=5)
        self.assertEqual(monitored_stream, stream_lines)

        analytics_report = self.analytics.generate_metrics_report(repo_path)
        self.assertEqual(analytics_report["report"], "generated")
        self.assertEqual(analytics_report["path"], repo_path)

        processed_pulse = self.engine.collect_and_process_pulse(
            repo_path=repo_path,
            run_id=run_id,
            metric=pulse_metric
        )
        self.assertEqual(processed_pulse["status"], "success")
        self.assertEqual(processed_pulse["run_id"], run_id)
        self.assertEqual(processed_pulse["metric"], pulse_metric)
        self.assertEqual(processed_pulse["repo_path"], repo_path)

if __name__ == "__main__":
    unittest.main()