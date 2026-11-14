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
    PulseException
)

class TestRepoHealthPulseEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.engine = RepoHealthPulseEngine()
        self.monitor = RepoMonitor()
        self.logger = RepoLogger()
        self.analytics = RepoAnalytics()
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_pulse_engine_full_integration_pipeline(self):
        repo_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())
        metric_name = f"security_violation_rate_{random.randint(100, 999)}"
        repo_path = os.path.join(self.test_dir.name, f"repo_{uuid.uuid4().hex[:8]}")
        os.makedirs(repo_path, exist_ok=True)

        monitor_result = self.monitor.check_status(repo_path)
        self.assertEqual(monitor_result["status"], "ok")
        self.assertEqual(monitor_result["path"], repo_path)

        metric_obj = self.engine.collect_metric(repo_id, metric_name)
        self.assertEqual(metric_obj.repo_id, repo_id)
        self.assertEqual(metric_obj.name, metric_name)
        self.assertTrue(metric_obj.is_healthy)

        stream_file = os.path.join(self.test_dir.name, f"stream_{uuid.uuid4().hex[:8]}.log")
        random_payload_line = f"ALERT:{uuid.uuid4()}:{random.randint(1,