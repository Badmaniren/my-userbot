import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
import uuid
import random

from skills.anomaly_audit_hub import AnomalyAuditHub, AnomalyAuditHubError


class TestAnomalyAuditHubUnit(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.log_path = os.path.join(self.temp_dir.name, f"test_audit_{uuid.uuid4().hex}.log")
        self.threshold = random.uniform(1.0, 50.0)
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_attributes(self):
        self.assertEqual(self.hub.repo_path, self.repo_path)
        self.assertEqual(self.hub.log_path, self.log_path)
        self.assertEqual(self.hub.threshold, self.threshold)
        self.assertIsNotNone(self.hub.logger)
        self.assertIsNotNone(self.hub.aggregator)

    def test_log_anomaly_delegates_to_logger(self):
        with patch.object(self.hub.logger, 'log_anomaly') as mock_log:
            mock_log.return_value = {"status": "ok"}
            res = self.hub.log_anomaly(
                source="test_src",
                severity="HIGH",
                details={"msg": "test"},
                telemetry_snapshot={"cpu": 80}
            )
            mock_log.assert_called_once_with(
                source="test_src",
                severity="HIGH",
                details={"msg": "test"},
                telemetry_snapshot={"cpu": 80}
            )
            self.assertEqual(res, {"status": "ok"})

    def test_aggregate_and_report_delegates_to_aggregator(self):
        with patch.object(self.hub.aggregator, 'aggregate_and_report') as mock_agg:
            mock_agg.return_value = [{"anomaly": "detected"}]
            res = self.hub.aggregate_and_report("cpu_load", 95.5)
            mock_agg.assert_called_once_with(
                metric_name="cpu_load",
                value=95.5
            )
            self.assertEqual(res, [{"anomaly": "detected"}])

    def test_generate_final_report_delegates_to_aggregator(self):
        with patch.object(self.hub.aggregator, 'generate_final_report') as mock_report:
            mock_report.return_value = {"report": "final"}
            res = self.hub.generate_final_report()
            mock_report.assert_called_once()
            self.assertEqual(res, {"report": "final"})

    def test_error_wrapping(self):
        with patch.object(self.hub.logger, 'log_anomaly', side_effect=RuntimeError("logger crash")):
            with self.assertRaises(AnomalyAuditHubError):
                self.hub.log_anomaly("src", "LOW", {}, {})

        with patch.object(self.hub.aggregator, 'aggregate_and_report', side_effect=RuntimeError("aggregator crash")):
            with self.assertRaises(AnomalyAuditHubError):
                self.hub.aggregate_and_report("metric", 1.0)

        with patch.object(self.hub.aggregator, 'generate_final_report', side_effect=RuntimeError("report crash")):
            with self.assertRaises(AnomalyAuditHubError):
                self.hub.generate_final_report()


if __name__ == "__main__":
    unittest.main()
