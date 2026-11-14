import unittest
import tempfile
import os
import uuid
import random
from skills.repo_health_pulse_engine import RepoHealthPulseEngine, RepoMonitor, RepoLogger, RepoAnalytics

class TestRepoHealthPulseEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.engine = RepoHealthPulseEngine()
        self.monitor = RepoMonitor()
        self.logger = RepoLogger()
        self.analytics = RepoAnalytics()
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_pulse_pipeline_integration(self):
        repo_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())
        metric_name = f"security_metric_{random.randint(1000, 9999)}"
        repo_path = self.test_dir.name
        
        target_file = os.path.join(repo_path, f"log_{uuid.uuid4()}.txt")
        log_message = f"Audit run {run_id} for repo {repo_id}"
        
        log_success = self.logger.log_event(target_file, log_message)
        self.assertTrue(log_success)
        self.assertTrue(os.path.exists(target_file))
        
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        self.assertEqual(content, log_message)

        monitor_result = self.monitor.check_status(repo_path)
        self.assertEqual(monitor_result["status"], "ok")
        self.assertEqual(monitor_result["path"], repo_path)

        analytics_report = self.analytics.generate_metrics_report(repo_path)
        self.assertEqual(analytics_report["report"], "generated")
        self.assertEqual(analytics_report["path"], repo_path)

        pulse_metric = self.engine.collect_metric(repo_id, metric_name)
        self.assertEqual(pulse_metric.repo_id, repo_id)
        self.assertEqual(pulse_metric.name, metric_name)
        self.assertTrue(pulse_metric.is_healthy)
        self.assertIsNotNone(pulse_metric.value)

        stream_file = os.path.join(repo_path, f"stream_{uuid.uuid4()}.log")
        stream_lines = [f"line_{uuid.uuid4()}" for _ in range(3)]
        with open(stream_file, "w", encoding="utf-8") as sf:
            sf.write("\n".join(stream_lines) + "\n")

        monitored_stream = self.engine.monitor_stream(stream_file, limit=5)
        self.assertEqual(monitored_stream, stream_lines)

        processed_pulse = self.engine.collect_and_process_pulse(
            repo_path=repo_path,
            run_id=run_id,
            metric=pulse_metric
        )
        
        self.assertEqual(processed_pulse["status"], "success")
        self.assertEqual(processed_pulse["run_id"], run_id)
        self.assertEqual(processed_pulse["repo_path"], repo_path)
        self.assertEqual(processed_pulse["metric"].repo_id, repo_id)

if __name__ == "__main__":
    unittest.main()