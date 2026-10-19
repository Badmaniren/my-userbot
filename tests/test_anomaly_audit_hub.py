import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHub(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 0.95)

        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def test_init_sets_dependencies_correctly(self):
        self.assertEqual(self.hub.logger.log_path, self.log_path)
        self.assertEqual(self.hub.aggregator.repo_path, self.repo_path)
        self.assertEqual(self.hub.aggregator.log_path, self.log_path)
        self.assertEqual(self.hub.aggregator.threshold, self.threshold)
        self.assertEqual(self.hub.aggregator.logger, self.hub.logger)

    def test_log_anomaly_delegates_to_logger(self):
        source = "".join(random.choices(string.ascii_letters, k=10))
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {uuid.uuid4().hex: random.randint(1, 100)}
        telemetry_snapshot = {uuid.uuid4().hex: random.random()}

        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.anomaly_logger.AnomalyLogger.log_anomaly") as mock_log:
            mock_log.return_value = expected_result

            result = self.hub.log_anomaly(
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

    def test_aggregate_and_report_delegates_to_aggregator(self):
        metric_name = uuid.uuid4().hex
        value = random.uniform(1.0, 100.0)
        expected_report = {uuid.uuid4().hex: random.uniform(0, 1)}

        with patch("skills.anomaly_report_aggregator.AnomalyReportAggregator.aggregate_and_report") as mock_agg:
            mock_agg.return_value = expected_report

            result = self.hub.aggregate_and_report(
                metric_name=metric_name,
                value=value
            )

            mock_agg.assert_called_once_with(
                metric_name=metric_name,
                value=value
            )
            self.assertEqual(result, expected_report)

    def test_generate_final_report_delegates_to_aggregator(self):
        expected_final_report = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "threshold": self.threshold
        }

        with patch("skills.anomaly_report_aggregator.AnomalyReportAggregator.generate_final_report") as mock_gen:
            mock_gen.return_value = expected_final_report

            result = self.hub.generate_final_report()

            mock_gen.assert_called_once()
            self.assertEqual(result, expected_final_report)


if __name__ == "__main__":
    unittest.main()