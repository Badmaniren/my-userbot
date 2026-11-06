import unittest
import tempfile
import pathlib
import uuid
import random
import json
from skills.repo_health_pulse import (
    RepoHealthPulseCollector,
    RepoHealthTrendAnalyzer,
    RepoHealthMetric,
    RepoHealthDegradationError,
    repo_health_pulse
)
from skills.repo_monitor import repo_monitor
from skills.repo_auditor import repo_auditor
from skills.repo_analytics import repo_analytics
from skills.repo_logger import repo_logger


class TestRepoHealthPulseIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.run_id = f"run_{uuid.uuid4().hex}"
        self.collector = RepoHealthPulseCollector(self.repo_path)
        self.analyzer = RepoHealthTrendAnalyzer()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_integration_full_health_pulse_pipeline(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric = self.collector.collect_metric(metric_name)
        self.assertEqual(metric.name, metric_name)
        self.assertIsInstance(metric.value, float)

        stream_filename = f"stream_{uuid.uuid4().hex[:8]}.txt"
        stream_path = pathlib.Path(self.repo_path) / stream_filename
        
        rand_int = random.randint(10, 100)
        rand_float = round(random.uniform(1.0, 50.0), 2)
        rand_str = f"status_{uuid.uuid4().hex[:6]}"
        
        stream_content = f"cpu_load: {rand_int}\nmemory_usage: {rand_float}\nnode_state: {rand_str}\n"
        stream_path.write_text(stream_content, encoding='utf-8')

        parsed_data = self.collector.parse_health_stream(stream_filename)
        self.assertEqual(parsed_data.get("cpu_load"), rand_int)
        self.assertEqual(parsed_data.get("memory_usage"), rand_float)
        self.assertEqual(parsed_data.get("node_state"), rand_str)

        threshold = random.uniform(50.0, 100.0)
        try:
            self.collector.enforce_health_guard(threshold)
        except RepoHealthDegradationError as e:
            self.assertIn("Health threshold exceeded", str(e))

        metrics_list = [
            RepoHealthMetric(name="m1", value=float(random.randint(10, 20))),
            RepoHealthMetric(name="m2", value=float(random.randint(25, 40))),
            RepoHealthMetric(name="m3", value=float(random.randint(90, 120)))
        ]
        trend_detected = self.analyzer.analyze_trend(metrics_list)
        self.assertTrue(trend_detected)

        analytics_score = random.randint(0, 100)
        analytics_payload = {
            "analytics_score": analytics_score,
            "source": f"source_{uuid.uuid4().hex[:6]}"
        }

        result = repo_health_pulse(self.repo_path, analytics_payload, self.run_id)

        self.assertEqual(result["run_id"], self.run_id)
        self.assertEqual(result["analytics"]["analytics_score"], analytics_score)
        
        if analytics_score < 20:
            self.assertEqual(result["status"], "critical")
        elif analytics_score < 50:
            self.assertEqual(result["status"], "degraded")
        else:
            self.assertEqual(result["status"], "healthy")

        expected_report_path = pathlib.Path(self.repo_path) / f"health_report_{self.run_id}.json"
        self.assertTrue(expected_report_path.exists())

        file_content = json.loads(expected_report_path.read_text(encoding='utf-8'))
        self.assertEqual(file_content["run_id"], self.run_id)
        self.assertEqual(file_content["status"], result["status"])
        self.assertEqual(file_content["analytics"]["analytics_score"], analytics_score)


if __name__ == "__main__":
    unittest.main()