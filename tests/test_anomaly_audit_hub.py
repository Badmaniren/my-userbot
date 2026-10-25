import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHub(unittest.TestCase):

    def setUp(self):
        self.random_repo = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.random_log = f"/tmp/{uuid.uuid4().hex}.log"
        self.random_threshold = round(random.uniform(0.1, 99.9), 3)

        with patch("skills.anomaly_audit_hub.AnomalyLogger") as mock_logger_cls, \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator") as mock_aggregator_cls:

            self.mock_logger_instance = mock_logger_cls.return_value
            self.mock_aggregator_instance = mock_aggregator_cls.return_value

            self.audit_hub = AnomalyAuditHub(
                repo_path=self.random_repo,
                log_path=self.random_log,
                threshold=self.random_threshold
            )

    def test_init_initializes_dependencies_correctly(self):
        with patch("skills.anomaly_audit_hub.AnomalyLogger") as mock_logger_cls, \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator") as mock_aggregator_cls:

            repo = uuid.uuid4().hex
            log = uuid.uuid4().hex
            threshold = random.random()

            AnomalyAuditHub(repo_path=repo, log_path=log, threshold=threshold)

            mock_logger_cls.assert_called_once_with(log_path=log)
            mock_aggregator_cls.assert_called_once_with(
                repo_path=repo,
                log_path=log,
                threshold=threshold,
                logger=mock_logger_cls.return_value
            )

    def test_log_anomaly_delegates_to_logger(self):
        source = uuid.uuid4().hex
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_snapshot = {uuid.uuid4().hex: random.randint(0, 1000)}

        expected_result = uuid.uuid4().hex
        self.mock_logger_instance.log_anomaly.return_value = expected_result

        result = self.audit_hub.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.mock_logger_instance.log_anomaly.assert_called_once_with(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        self.assertEqual(result, expected_result)

    def test_aggregate_and_report_delegates_to_aggregator(self):
        metric_name = uuid.uuid4().hex
        value = random.uniform(-1000.0, 1000.0)

        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_aggregator_instance.aggregate_and_report.return_value = expected_result

        result = self.audit_hub.aggregate_and_report(
            metric_name=metric_name,
            value=value
        )

        self.mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
            metric_name=metric_name,
            value=value
        )
        self.assertEqual(result, expected_result)

    def test_generate_final_report_delegates_to_aggregator(self):
        expected_report = [uuid.uuid4().hex, uuid.uuid4().hex]
        self.mock_aggregator_instance.generate_final_report.return_value = expected_report

        result = self.audit_hub.generate_final_report()

        self.mock_aggregator_instance.generate_final_report.assert_called_once()
        self.assertEqual(result, expected_report)


if __name__ == "__main__":
    unittest.main()