import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHub(unittest.TestCase):
    def setUp(self):
        self.rand_repo = f"/repo/{uuid.uuid4().hex}"
        self.rand_log = f"/var/log/{uuid.uuid4().hex}.log"
        self.rand_threshold = round(random.uniform(0.1, 99.9), 2)

        self.hub = AnomalyAuditHub(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

    def test_init_sets_correct_attributes(self):
        self.assertEqual(self.hub.logger.log_path, self.rand_log)
        self.assertEqual(self.hub.aggregator.repo_path, self.rand_repo)
        self.assertEqual(self.hub.aggregator.threshold, self.rand_threshold)

    def test_log_anomaly_delegates_to_logger(self):
        rand_source = ''.join(random.choices(string.ascii_lowercase, k=10))
        rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rand_details = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_snapshot = {uuid.uuid4().hex: random.randint(1, 1000)}
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.anomaly_logger.AnomalyLogger.log_anomaly", return_value=expected_result) as mock_log:
            result = self.hub.log_anomaly(
                source=rand_source,
                severity=rand_severity,
                details=rand_details,
                telemetry_snapshot=rand_snapshot
            )

            mock_log.assert_called_once_with(
                source=rand_source,
                severity=rand_severity,
                details=rand_details,
                telemetry_snapshot=rand_snapshot
            )
            self.assertEqual(result, expected_result)

    def test_aggregate_and_report_delegates_to_aggregator(self):
        rand_metric = ''.join(random.choices(string.ascii_uppercase, k=8))
        rand_value = round(random.uniform(1.0, 500.0), 2)
        expected_aggregation = {uuid.uuid4().hex: random.random()}

        with patch("skills.anomaly_report_aggregator.AnomalyReportAggregator.aggregate_and_report", return_value=expected_aggregation) as mock_agg:
            result = self.hub.aggregate_and_report(
                metric_name=rand_metric,
                value=rand_value
            )

            mock_agg.assert_called_once_with(
                metric_name=rand_metric,
                value=rand_value
            )
            self.assertEqual(result, expected_aggregation)

    def test_generate_final_report_delegates_to_aggregator(self):
        expected_report = {
            "report_id": uuid.uuid4().hex,
            "status": random.choice(["SECURE", "VULNERABLE", "WARNING"]),
            "score": random.randint(0, 100)
        }

        with patch("skills.anomaly_report_aggregator.AnomalyReportAggregator.generate_final_report", return_value=expected_report) as mock_report:
            result = self.hub.generate_final_report()

            mock_report.assert_called_once()
            self.assertEqual(result, expected_report)

if __name__ == '__main__':
    unittest.main()