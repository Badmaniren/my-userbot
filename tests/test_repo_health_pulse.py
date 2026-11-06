import unittest
from unittest.mock import patch
import json
import pathlib
import uuid
import random
import io
import subprocess

from skills.repo_health_pulse import (
    RepoHealthDegradationError,
    RepoHealthMetric,
    RepoHealthPulseCollector,
    RepoHealthTrendAnalyzer,
    repo_health_pulse,
)


class TestRepoHealthPulse(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.stream_name = f"stream_{uuid.uuid4().hex[:8]}.txt"
        self.run_id = uuid.uuid4().hex[:8]

    def test_repo_health_metric_dataclass(self):
        val = random.uniform(1.0, 100.0)
        detail_key = uuid.uuid4().hex
        detail_val = uuid.uuid4().hex
        metric = RepoHealthMetric(name=self.metric_name, value=val, details={detail_key: detail_val})
        self.assertEqual(metric.name, self.metric_name)
        self.assertEqual(metric.value, val)
        self.assertEqual(metric.details[detail_key], detail_val)

    def test_collector_collect_metric_success(self):
        collector = RepoHealthPulseCollector(repo_path=self.repo_path)
        expected_value = round(random.uniform(10.0, 90.0), 2)
        mock_output = json.dumps({"metric": self.metric_name, "value": expected_value, "details": {"info": uuid.uuid4().hex}})
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = mock_output
            mock_run.return_value.stderr = ""
            
            metric = collector.collect_metric(self.metric_name)
            self.assertEqual(metric.name, self.metric_name)
            self.assertEqual(metric.value, expected_value)
            mock_run.assert_called_once()

    def test_collector_collect_metric_failure(self):
        collector = RepoHealthPulseCollector(repo_path=self.repo_path)
        err_msg = uuid.uuid4().hex
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = err_msg.encode('utf-8')
            
            with self.assertRaises(RepoHealthDegradationError):
                collector.collect_metric(self.metric_name)

    def test_collector_parse_health_stream(self):
        key1 = uuid.uuid4().hex[:6]
        val1 = random.randint(1, 1000)
        key2 = uuid.uuid4().hex[:6]
        val2 = round(random.uniform(0.1, 100.0), 2)
        key3 = uuid.uuid4().hex[:6]
        val3 = uuid.uuid4().hex

        stream_content = f"{key1}: {val1}\n{key2}: {val2}\n{key3}: {val3}\n".encode('utf-8')
        
        collector = RepoHealthPulseCollector(repo_path=self.repo_path)
        with patch("pathlib.Path.open", return_value=io.BytesIO(stream_content), create=True):
            parsed = collector.parse_health_stream(self.stream_name)
            self.assertEqual(parsed[key1], val1)
            self.assertEqual(parsed[key2], val2)
            self.assertEqual(parsed[key3], val3)

    def test_collector_enforce_health_guard_success(self):
        collector = RepoHealthPulseCollector(repo_path=self.repo_path)
        threshold = random.uniform(50.0, 100.0)
        safe_value = threshold - random.uniform(1.0, 10.0)
        
        metric = RepoHealthMetric(name="guard_metric", value=safe_value)
        with patch.object(collector, "collect_metric", return_value=metric) as mock_collect:
            collector.enforce_health_guard(threshold)
            mock_collect.assert_called_once_with("guard_metric")

    def test_collector_enforce_health_guard_failure(self):
        collector = RepoHealthPulseCollector(repo_path=self.repo_path)
        threshold = random.uniform(10.0, 50.0)
        unsafe_value = threshold + random.uniform(1.0, 10.0)
        
        metric = RepoHealthMetric(name="guard_metric", value=unsafe_value)
        with patch.object(collector, "collect_metric", return_value=metric):
            with self.assertRaises(RepoHealthDegradationError):
                collector.enforce_health_guard(threshold)

    def test_trend_analyzer_insufficient_metrics(self):
        analyzer = RepoHealthTrendAnalyzer()
        self.assertFalse(analyzer.analyze_trend([]))
        self.assertFalse(analyzer.analyze_trend([RepoHealthMetric(name=self.metric_name, value=10.0)]))

    def test_trend_analyzer_spike_detected(self):
        analyzer = RepoHealthTrendAnalyzer()
        metrics = [
            RepoHealthMetric(name=self.metric_name, value=10.0),
            RepoHealthMetric(name=self.metric_name, value=12.0),
            RepoHealthMetric(name=self.metric_name, value=11.0),
            RepoHealthMetric(name=self.metric_name, value=65.0),
        ]
        self.assertTrue(analyzer.analyze_trend(metrics))

    def test_trend_analyzer_steady_increase_detected(self):
        analyzer = RepoHealthTrendAnalyzer()
        metrics = [
            RepoHealthMetric(name=self.metric_name, value=10.0),
            RepoHealthMetric(name=self.metric_name, value=20.0),
            RepoHealthMetric(name=self.metric_name, value=30.0),
            RepoHealthMetric(name=self.metric_name, value=45.0),
        ]
        self.assertTrue(analyzer.analyze_trend(metrics))

    def test_trend_analyzer_healthy_trend(self):
        analyzer = RepoHealthTrendAnalyzer()
        metrics = [
            RepoHealthMetric(name=self.metric_name, value=50.0),
            RepoHealthMetric(name=self.metric_name, value=48.0),
            RepoHealthMetric(name=self.metric_name, value=49.0),
            RepoHealthMetric(name=self.metric_name, value=47.0),
        ]
        self.assertFalse(analyzer.analyze_trend(metrics))

    def test_repo_health_pulse_healthy_status(self):
        analytics_key = uuid.uuid4().hex
        analytics_val = uuid.uuid4().hex
        score = random.randint(50, 100)
        analytics = {"analytics_score": score, analytics_key: analytics_val}

        with patch("pathlib.Path.write_text") as mock_write:
            result = repo_health_pulse(self.repo_path, analytics, self.run_id)
            self.assertEqual(result["status"], "healthy")
            self.assertEqual(result["run_id"], self.run_id)
            self.assertEqual(result["analytics"]["analytics_score"], score)
            mock_write.assert_called_once()

    def test_repo_health_pulse_degraded_status(self):
        score = random.randint(20, 49)
        analytics = {"analytics_score": score}

        with patch("pathlib.Path.write_text") as mock_write:
            result = repo_health_pulse(self.repo_path, analytics, self.run_id)
            self.assertEqual(result["status"], "degraded")
            mock_write.assert_called_once()

    def test_repo_health_pulse_critical_status(self):
        score = random.randint(0, 19)
        analytics = {"analytics_score": score}

        with patch("pathlib.Path.write_text") as mock_write:
            result = repo_health_pulse(self.repo_path, analytics, self.run_id)
            self.assertEqual(result["status"], "critical")
            mock_write.assert_called_once()