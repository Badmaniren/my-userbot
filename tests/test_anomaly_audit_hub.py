import unittest
from unittest.mock import patch
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHub(unittest.TestCase):

    def setUp(self):
        self.random_repo = f"/repo_{uuid.uuid4().hex[:8]}"
        self.random_log = f"/var/log/{uuid.uuid4().hex[:8]}.log"
        self.random_threshold = random.uniform(0.1, 99.9)
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.random_repo,
            log_path=self.random_log,
            threshold=self.random_threshold
        )

    def test_init_sets_components(self):
        self.assertIsNotNone(self.audit_hub.logger)
        self.assertIsNotNone(self.audit_hub.aggregator)
        self.assertEqual(self.audit_hub.logger.log_path, self.random_log)
        self.assertEqual(self.audit_hub.aggregator.repo_path, self.random_repo)
        self.assertEqual(self.audit_hub.aggregator.threshold, self.random_threshold)

    def test_log_anomaly_delegates_correctly(self):
        source = f"source_{uuid.uuid4().hex[:6]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}
        telemetry_snapshot = {uuid.uuid4().hex: random.random() for _ in range(2)}
        expected_result = f"logged_{uuid.uuid4().hex}"

        with patch("skills.anomaly_logger.AnomalyLogger.log_anomaly", return_value=expected_result) as mock_log:
            result = self.audit_hub.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )

            mock_log.assert_called_once_with(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )
            self.assertEqual(result, expected_result)

    def test_aggregate_and_report_delegates_correctly(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        value = random.uniform(1.0, 1000.0)
        expected_result = {"status": uuid.uuid4().hex, "value": value}

        with patch("skills.anomaly_report_aggregator.AnomalyReportAggregator.aggregate_and_report", return_value=expected_result) as mock_aggregate:
            result = self.audit_hub.aggregate_and_report(
                metric_name=metric_name,
                value=value
            )

            mock_aggregate.assert_called_once_with(
                metric_name=metric_name,
                value=value
            )
            self.assertEqual(result, expected_result)

    def test_generate_final_report_delegates_correctly(self):
        expected_report = {
            "audit_id": uuid.uuid4().hex,
            "anomalies_found": random.randint(0, 50),
            "summary": ''.join(random.choices(string.ascii_letters, k=10))
        }

        with patch("skills.anomaly_report_aggregator.AnomalyReportAggregator.generate_final_report", return_value=expected_report) as mock_generate:
            result = self.audit_hub.generate_final_report()

            mock_generate.assert_called_once()
            self.assertEqual(result, expected_report)

if __name__ == "__main__":
    unittest.main()