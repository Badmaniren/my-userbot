import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHub(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/repo/{uuid.uuid4().hex}"
        self.rand_log = f"/logs/{uuid.uuid4().hex}.log"
        self.rand_threshold = random.uniform(0.1, 99.9)

        with patch("skills.anomaly_audit_hub.AnomalyLogger") as mock_logger_cls, \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator") as mock_aggregator_cls:

            self.mock_logger_instance = mock_logger_cls.return_value
            self.mock_aggregator_instance = mock_aggregator_cls.return_value

            self.hub = AnomalyAuditHub(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.rand_threshold
            )

    def test_init_initialization(self):
        rand_repo_local = f"/var/repo/{uuid.uuid4().hex}"
        rand_log_local = f"/var/log/{uuid.uuid4().hex}.log"
        rand_threshold_local = random.uniform(1.0, 50.0)

        with patch("skills.anomaly_audit_hub.AnomalyLogger") as mock_logger_cls, \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator") as mock_aggregator_cls:

            AnomalyAuditHub(
                repo_path=rand_repo_local,
                log_path=rand_log_local,
                threshold=rand_threshold_local
            )

            mock_logger_cls.assert_called_once_with(log_path=rand_log_local)
            mock_aggregator_cls.assert_called_once_with(
                repo_path=rand_repo_local,
                log_path=rand_log_local,
                threshold=rand_threshold_local,
                logger=mock_logger_cls.return_value
            )

    def test_log_anomaly_delegates_correctly(self):
        rand_source = ''.join(random.choices(string.ascii_letters, k=10))
        rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rand_details_key = uuid.uuid4().hex
        rand_details_val = uuid.uuid4().hex
        rand_telemetry_key = uuid.uuid4().hex
        rand_telemetry_val = random.randint(100, 999)

        details = {rand_details_key: rand_details_val}
        telemetry_snapshot = {rand_telemetry_key: rand_telemetry_val}

        expected_return = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_logger_instance.log_anomaly.return_value = expected_return

        result = self.hub.log_anomaly(
            source=rand_source,
            severity=rand_severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.mock_logger_instance.log_anomaly.assert_called_once_with(
            source=rand_source,
            severity=rand_severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        self.assertEqual(result, expected_return)

    def test_aggregate_and_report_delegates_correctly(self):
        rand_metric = f"metric_{uuid.uuid4().hex[:6]}"
        rand_value = random.uniform(-1000.0, 1000.0)
        expected_aggregate_result = {uuid.uuid4().hex: random.random()}

        self.mock_aggregator_instance.aggregate_and_report.return_value = expected_aggregate_result

        result = self.hub.aggregate_and_report(
            metric_name=rand_metric,
            value=rand_value
        )

        self.mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
            metric_name=rand_metric,
            value=rand_value
        )
        self.assertEqual(result, expected_aggregate_result)

    def test_generate_final_report_delegates_correctly(self):
        expected_report = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "status": random.choice(["SECURE", "VULNERABLE", "UNKNOWN"])
        }
        self.mock_aggregator_instance.generate_final_report.return_value = expected_report

        result = self.hub.generate_final_report()

        self.mock_aggregator_instance.generate_final_report.assert_called_once()
        self.assertEqual(result, expected_report)


if __name__ == '__main__':
    unittest.main()