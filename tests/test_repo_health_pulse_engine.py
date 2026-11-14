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
        self.repo_id = uuid.uuid4().hex
        self.metric_name = uuid.uuid4().hex
        self.stream_path = f"{uuid.uuid4().hex}.txt"
        self.url = f"https://{uuid.uuid4().hex}.internal/pulse"

    def test_pulse_metric_dataclass_defaults(self):
        metric = PulseMetric(repo_id=self.repo_id, name=self.metric_name)
        self.assertEqual(metric.repo_id, self.repo_id)
        self.assertEqual(metric.name, self.metric_name)
        self.assertIsNone(metric.value)
        self.assertTrue(metric.is_healthy)
        self.assertEqual(metric.error_message, "")

    def test_repo_monitor_check_status(self):
        monitor = RepoMonitor()
        path = uuid.uuid4().hex
        result = monitor.check_status(path)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["path"], path)

    def test_repo_logger_log_event(self):
        logger = RepoLogger()
        target_file = f"{uuid.uuid4().hex}.log"
        message = uuid.uuid4().hex

        with patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file:
            success = logger.log_event(target_file, message)
            self.assertTrue(success)
            mock_file.assert_called_once_with(target_file, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(message + "\n")

    def test_repo_analytics_generate_metrics_report(self):
        analytics = RepoAnalytics()
        path = uuid.uuid4().hex
        report = analytics.generate_metrics_report(path)
        self.assertEqual(report["report"], "generated")
        self.assertEqual(report["path"], path)

    def test_collect_metric_success(self):
        expected_value = random.uniform(1.0, 100.0)
        with patch.object(self.engine, "_fetch_raw_metric", return_value=expected_value) as mock_fetch:
            metric = self.engine.collect_metric(self.repo_id, self.metric_name)
            mock_fetch.assert_called_once_with(self.repo_id, self.metric_name)
            self.assertEqual(metric.repo_id, self.repo_id)
            self.assertEqual(metric.name, self.metric_name)
            self.assertEqual(metric.value, expected_value)
            self.assertTrue(metric.is_healthy)
            self.assertEqual(metric.error_message, "")

    def test_collect_metric_failure(self):
        error_msg = uuid.uuid4().hex
        with patch.object(self.engine, "_fetch_raw_metric", side_effect=Exception(error_msg)) as mock_fetch:
            metric = self.engine.collect_metric(self.repo_id, self.metric_name)
            mock_fetch.assert_called_once_with(self.repo_id, self.metric_name)
            self.assertEqual(metric.repo_id, self.repo_id)
            self.assertEqual(metric.name, self.metric_name)
            self.assertIsNone(metric.value)
            self.assertFalse(metric.is_healthy)
            self.assertEqual(metric.error_message, error_msg)

    def test_monitor_stream_parsing(self):
        line1 = uuid.uuid4().hex
        line2 = uuid.uuid4().hex
        file_content = f"{line1}\n{line2}\n"
        limit = random.randint(1, 5)

        mock_file_data = io.StringIO(file_content)
        with patch("builtins.open", return_value=mock_file_data):
            result = self.engine.monitor_stream(self.stream_path, limit=limit)
            self.assertIn(line1, result)
            self.assertIn(line2, result)
            self.assertLessEqual(len(result), limit)

    def test_export_pulse_success(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        response_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_response = MagicMock()
        mock_response.json.return_value = response_data

        with patch("requests.post", return_value=mock_response) as mock_post:
            res = self.engine.export_pulse(self.url, payload)
            mock_post.assert_called_once_with(self.url, json=payload)
            self.assertEqual(res, response_data)

    def test_export_pulse_exception(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        err_msg = uuid.uuid4().hex

        with patch("requests.post", side_effect=requests.RequestException(err_msg)) as mock_post:
            with self.assertRaises(PulseException) as ctx:
                self.engine.export_pulse(self.url, payload)
            mock_post.assert_called_once_with(self.url, json=payload)
            self.assertIn(err_msg, str(ctx.exception))

    def test_collect_and_process_pulse(self):
        repo_path = uuid.uuid4().hex
        run_id = uuid.uuid4().hex
        metric_payload = {uuid.uuid4().hex: random.randint(10, 50)}

        result = self.engine.collect_and_process_pulse(repo_path, run_id, metric_payload)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["run_id"], run_id)
        self.assertEqual(result["metric"], metric_payload)
        self.assertEqual(result["repo_path"], repo_path)