import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import io

from skills.repo_health_pulse_engine import (
    PulseException,
    PulseMetric,
    RepoMonitor,
    RepoLogger,
    RepoAnalytics,
    RepoHealthPulseEngine
)


class TestRepoHealthPulseEngine(unittest.TestCase):

    def test_pulse_exception_inheritance(self):
        self.assertTrue(issubclass(PulseException, Exception))

    def test_pulse_metric_dataclass_creation(self):
        repo_id = uuid.uuid4().hex
        name = uuid.uuid4().hex
        value = random.uniform(1.0, 100.0)
        is_healthy = random.choice([True, False])
        error_message = uuid.uuid4().hex

        metric = PulseMetric(
            repo_id=repo_id,
            name=name,
            value=value,
            is_healthy=is_healthy,
            error_message=error_message
        )

        self.assertEqual(metric.repo_id, repo_id)
        self.assertEqual(metric.name, name)
        self.assertEqual(metric.value, value)
        self.assertEqual(metric.is_healthy, is_healthy)
        self.assertEqual(metric.error_message, error_message)

    def test_repo_monitor_check_status(self):
        monitor = RepoMonitor()
        repo_path = uuid.uuid4().hex
        result = monitor.check_status(repo_path)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "ok")
        self.assertEqual(result.get("path"), repo_path)

    def test_repo_logger_log_event(self):
        logger = RepoLogger()
        target_file = uuid.uuid4().hex
        message = uuid.uuid4().hex

        with patch("builtins.open", mock_open()) as mock_file:
            success = logger.log_event(target_file, message)
            self.assertTrue(success)
            mock_file.assert_called_once_with(target_file, "w", encoding="utf-8")
            mock_file().write.assert_called_once_with(message + "\n")

    def test_repo_analytics_generate_metrics_report(self):
        analytics = RepoAnalytics()
        repo_path = uuid.uuid4().hex
        report = analytics.generate_metrics_report(repo_path)
        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("report"), "generated")
        self.assertEqual(report.get("path"), repo_path)

    def test_repo_health_pulse_engine_collect_metric_success(self):
        engine = RepoHealthPulseEngine()
        repo_id = uuid.uuid4().hex
        name = uuid.uuid4().hex
        expected_value = random.uniform(0.0, 1000.0)

        with patch.object(engine, "_fetch_raw_metric", return_value=expected_value) as mock_fetch:
            metric = engine.collect_metric(repo_id, name)
            mock_fetch.assert_called_once_with(repo_id, name)
            self.assertEqual(metric.repo_id, repo_id)
            self.assertEqual(metric.name, name)
            self.assertEqual(metric.value, expected_value)
            self.assertTrue(metric.is_healthy)
            self.assertEqual(metric.error_message, "")

    def test_repo_health_pulse_engine_collect_metric_failure(self):
        engine = RepoHealthPulseEngine()
        repo_id = uuid.uuid4().hex
        name = uuid.uuid4().hex
        error_msg = uuid.uuid4().hex

        with patch.object(engine, "_fetch_raw_metric", side_effect=Exception(error_msg)) as mock_fetch:
            metric = engine.collect_metric(repo_id, name)
            mock_fetch.assert_called_once_with(repo_id, name)
            self.assertEqual(metric.repo_id, repo_id)
            self.assertEqual(metric.name, name)
            self.assertIsNone(metric.value)
            self.assertFalse(metric.is_healthy)
            self.assertEqual(metric.error_message, error_msg)

    def test_repo_health_pulse_engine_monitor_stream(self):
        engine = RepoHealthPulseEngine()
        stream_path = uuid.uuid4().hex
        line1 = uuid.uuid4().hex
        line2 = uuid.uuid4().hex
        file_content = f"{line1}\n{line2}\n"
        limit = random.randint(1, 10)

        with patch("builtins.open", mock_open(read_data=file_content)) as mock_file:
            metrics = engine.monitor_stream(stream_path, limit=limit)
            mock_file.assert_called_once_with(stream_path, 'r', encoding='utf-8')
            self.assertEqual(metrics, [line1, line2])

    def test_repo_health_pulse_engine_export_pulse_success(self):
        engine = RepoHealthPulseEngine()
        url = f"https://{uuid.uuid4().hex}.com/api"
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_response = {uuid.uuid4().hex: uuid.uuid4().hex}

        class MockResponse:
            def json(self):
                return expected_response

        with patch("requests.post", return_value=MockResponse()) as mock_post:
            result = engine.export_pulse(url, payload)
            mock_post.assert_called_once_with(url, json=payload)
            self.assertEqual(result, expected_response)

    def test_repo_health_pulse_engine_export_pulse_exception(self):
        engine = RepoHealthPulseEngine()
        url = f"https://{uuid.uuid4().hex}.com/api"
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        error_msg = uuid.uuid4().hex

        with patch("requests.post", side_effect=Exception(error_msg)) as mock_post:
            with self.assertRaises(PulseException) as ctx:
                engine.export_pulse(url, payload)
            mock_post.assert_called_once_with(url, json=payload)
            self.assertIn(error_msg, str(ctx.exception))

    def test_repo_health_pulse_engine_collect_and_process_pulse(self):
        engine = RepoHealthPulseEngine()
        repo_path = uuid.uuid4().hex
        run_id = uuid.uuid4().hex
        metric = {uuid.uuid4().hex: random.randint(1, 100)}

        result = engine.collect_and_process_pulse(repo_path, run_id, metric)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("run_id"), run_id)
        self.assertEqual(result.get("metric"), metric)
        self.assertEqual(result.get("repo_path"), repo_path)