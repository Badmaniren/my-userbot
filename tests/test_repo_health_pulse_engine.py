import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import requests

from skills.repo_health_pulse_engine import (
    PulseException,
    PulseMetric,
    RepoMonitor,
    RepoLogger,
    RepoAnalytics,
    RepoHealthPulseEngine
)

class TestRepoHealthPulseEngine(unittest.TestCase):

    def setUp(self):
        self.engine = RepoHealthPulseEngine()
        self.monitor = RepoMonitor()
        self.logger = RepoLogger()
        self.analytics = RepoAnalytics()
        self.random_repo_id = uuid.uuid4().hex
        self.random_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.random_url = f"https://{uuid.uuid4().hex[:10]}.com/pulse"

    def test_pulse_exception_inheritance(self):
        self.assertTrue(issubclass(PulseException, Exception))

    def test_pulse_metric_dataclass_defaults(self):
        metric = PulseMetric(repo_id=self.random_repo_id, name=self.random_metric_name)
        self.assertEqual(metric.repo_id, self.random_repo_id)
        self.assertEqual(metric.name, self.random_metric_name)
        self.assertIsNone(metric.value)
        self.assertTrue(metric.is_healthy)
        self.assertEqual(metric.error_message, "")

    def test_repo_monitor_check_status(self):
        res = self.monitor.check_status(self.random_path)
        self.assertEqual(res.get("status"), "ok")
        self.assertEqual(res.get("path"), self.random_path)

    def test_repo_logger_log_event(self):
        random_message = f"log_msg_{uuid.uuid4().hex}"
        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            result = self.logger.log_event(self.random_path, random_message)
            self.assertTrue(result)
            mock_file.assert_called_once_with(self.random_path, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(random_message + "\n")

    def test_repo_analytics_generate_metrics_report(self):
        report = self.analytics.generate_metrics_report(self.random_path)
        self.assertEqual(report.get("report"), "generated")
        self.assertEqual(report.get("path"), self.random_path)

    def test_repo_health_pulse_engine_fetch_raw_metric(self):
        val = self.engine._fetch_raw_metric(self.random_repo_id, self.random_metric_name)
        self.assertEqual(val, 0.0)

    def test_collect_metric_success(self):
        expected_value = round(random.uniform(1.0, 100.0), 2)
        with patch.object(self.engine, "_fetch_raw_metric", return_value=expected_value):
            metric = self.engine.collect_metric(self.random_repo_id, self.random_metric_name)
            self.assertEqual(metric.repo_id, self.random_repo_id)
            self.assertEqual(metric.name, self.random_metric_name)
            self.assertEqual(metric.value, expected_value)
            self.assertTrue(metric.is_healthy)
            self.assertEqual(metric.error_message, "")

    def test_collect_metric_failure(self):
        error_msg = f"err_{uuid.uuid4().hex}"
        with patch.object(self.engine, "_fetch_raw_metric", side_effect=Exception(error_msg)):
            metric = self.engine.collect_metric(self.random_repo_id, self.random_metric_name)
            self.assertEqual(metric.repo_id, self.random_repo_id)
            self.assertEqual(metric.name, self.random_metric_name)
            self.assertIsNone(metric.value)
            self.assertFalse(metric.is_healthy)
            self.assertEqual(metric.error_message, error_msg)

    def test_monitor_stream_success(self):
        lines = [f"line_{uuid.uuid4().hex}\n" for _ in range(3)]
        fake_file_content = "".join(lines)
        limit = random.randint(1, 5)

        with patch("builtins.open", return_value=io.StringIO(fake_file_content)):
            result = self.engine.monitor_stream(self.random_path, limit=limit)
            expected_count = min(len(lines), limit)
            self.assertEqual(len(result), expected_count)
            for i in range(expected_count):
                self.assertEqual(result[i], lines[i].strip())

    def test_export_pulse_success(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_response = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_resp = MagicMock()
        mock_resp.json.return_value = expected_response

        with patch("requests.post", return_value=mock_resp) as mock_post:
            res = self.engine.export_pulse(self.random_url, payload)
            mock_post.assert_called_once_with(self.random_url, json=payload)
            self.assertEqual(res, expected_response)

    def test_export_pulse_exception(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        error_msg = f"network_error_{uuid.uuid4().hex}"

        with patch("requests.post", side_effect=requests.RequestException(error_msg)):
            with self.assertRaises(PulseException) as ctx:
                self.engine.export_pulse(self.random_url, payload)
            self.assertIn(error_msg, str(ctx.exception))

    def test_collect_and_process_pulse(self):
        run_id = uuid.uuid4().hex
        metric_obj = PulseMetric(repo_id=self.random_repo_id, name=self.random_metric_name, value=random.random())

        result = self.engine.collect_and_process_pulse(self.random_path, run_id, metric_obj)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("run_id"), run_id)
        self.assertEqual(result.get("metric"), metric_obj)
        self.assertEqual(result.get("repo_path"), self.random_path)

if __name__ == "__main__":
    unittest.main()