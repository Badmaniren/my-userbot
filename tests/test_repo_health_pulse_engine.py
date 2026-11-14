import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string

from skills.repo_health_pulse_engine import (
    PulseException,
    PulseMetric,
    RepoMonitor,
    RepoLogger,
    RepoAnalytics,
    RepoHealthPulseEngine
)


class TestRepoHealthPulseEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = RepoHealthPulseEngine()
        self.repo_monitor = RepoMonitor()
        self.repo_logger = RepoLogger()
        self.repo_analytics = RepoAnalytics()

        self.rand_repo_id = uuid.uuid4().hex
        self.rand_metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.rand_path = f"/{''.join(random.choices(string.ascii_lowercase, k=6))}/{uuid.uuid4().hex}.log"
        self.rand_url = f"https://{''.join(random.choices(string.ascii_lowercase, k=8))}.local/api/v1/pulse"
        self.rand_run_id = uuid.uuid4().hex

    def test_pulse_metric_dataclass_defaults(self):
        metric = PulseMetric(repo_id=self.rand_repo_id, name=self.rand_metric_name)
        self.assertEqual(metric.repo_id, self.rand_repo_id)
        self.assertEqual(metric.name, self.rand_metric_name)
        self.assertIsNone(metric.value)
        self.assertTrue(metric.is_healthy)
        self.assertEqual(metric.error_message, "")

    def test_repo_monitor_check_status(self):
        res = self.repo_monitor.check_status(self.rand_path)
        self.assertEqual(res.get("status"), "ok")
        self.assertEqual(res.get("path"), self.rand_path)

    def test_repo_logger_log_event(self):
        rand_message = uuid.uuid4().hex
        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            success = self.repo_logger.log_event(self.rand_path, rand_message)
            self.assertTrue(success)
            mock_file.assert_called_once_with(self.rand_path, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(rand_message + "\n")

    def test_repo_analytics_generate_metrics_report(self):
        report = self.repo_analytics.generate_metrics_report(self.rand_path)
        self.assertEqual(report.get("report"), "generated")
        self.assertEqual(report.get("path"), self.rand_path)

    def test_collect_metric_success(self):
        expected_val = round(random.uniform(1.0, 100.0), 2)
        with patch.object(self.engine, "_fetch_raw_metric", return_value=expected_val) as mock_fetch:
            metric = self.engine.collect_metric(self.rand_repo_id, self.rand_metric_name)
            mock_fetch.assert_called_once_with(self.rand_repo_id, self.rand_metric_name)
            self.assertEqual(metric.repo_id, self.rand_repo_id)
            self.assertEqual(metric.name, self.rand_metric_name)
            self.assertEqual(metric.value, expected_val)
            self.assertTrue(metric.is_healthy)
            self.assertEqual(metric.error_message, "")

    def test_collect_metric_failure(self):
        err_msg = uuid.uuid4().hex
        with patch.object(self.engine, "_fetch_raw_metric", side_effect=Exception(err_msg)) as mock_fetch:
            metric = self.engine.collect_metric(self.rand_repo_id, self.rand_metric_name)
            mock_fetch.assert_called_once_with(self.rand_repo_id, self.rand_metric_name)
            self.assertEqual(metric.repo_id, self.rand_repo_id)
            self.assertEqual(metric.name, self.rand_metric_name)
            self.assertIsNone(metric.value)
            self.assertFalse(metric.is_healthy)
            self.assertEqual(metric.error_message, err_msg)

    def test_monitor_stream(self):
        lines_data = [uuid.uuid4().hex for _ in range(10)]
        stream_content = "\n".join(lines_data) + "\n"
        limit = random.randint(1, 5)

        mock_file_stream = io.BytesIO(stream_content.encode('utf-8'))
        
        with patch("builtins.open", return_value=io.TextIOWrapper(mock_file_stream, encoding='utf-8')):
            res = self.engine.monitor_stream(self.rand_path, limit=limit)
            self.assertEqual(len(res), limit)
            for i in range(limit):
                self.assertEqual(res[i], lines_data[i])

    def test_export_pulse_success(self):
        payload_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_resp = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_response = MagicMock()
        mock_response.json.return_value = expected_resp

        with patch("requests.post", return_value=mock_response) as mock_post:
            res = self.engine.export_pulse(self.rand_url, payload_data)
            mock_post.assert_called_once_with(self.rand_url, json=payload_data)
            self.assertEqual(res, expected_resp)

    def test_export_pulse_exception(self):
        payload_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        err_msg = uuid.uuid4().hex

        with patch("requests.post", side_effect=Exception(err_msg)) as mock_post:
            with self.assertRaises(PulseException) as ctx:
                self.engine.export_pulse(self.rand_url, payload_data)
            mock_post.assert_called_once_with(self.rand_url, json=payload_data)
            self.assertIn(err_msg, str(ctx.exception))

    def test_collect_and_process_pulse(self):
        dummy_metric = PulseMetric(repo_id=self.rand_repo_id, name=self.rand_metric_name, value=42.0)
        res = self.engine.collect_and_process_pulse(self.rand_path, self.rand_run_id, dummy_metric)
        self.assertEqual(res.get("status"), "success")
        self.assertEqual(res.get("run_id"), self.rand_run_id)
        self.assertEqual(res.get("repo_path"), self.rand_path)
        self.assertEqual(res.get("metric"), dummy_metric)


if __name__ == "__main__":
    unittest.main()