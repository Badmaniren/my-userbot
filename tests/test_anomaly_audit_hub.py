import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHub(unittest.TestCase):
    def setUp(self):
        self.rand_repo = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.rand_log = f"/tmp/{uuid.uuid4().hex}.log"
        self.rand_threshold = round(random.uniform(0.1, 99.9), 4)

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
        self.assertEqual(self.hub.logger, self.mock_logger_instance)
        self.assertEqual(self.hub.aggregator, self.mock_aggregator_instance)

    def test_log_anomaly_proxy(self):
        rand_source = ''.join(random.choices(string.ascii_letters, k=10))
        rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rand_details = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_telemetry = {uuid.uuid4().hex: random.random()}

        expected_return = uuid.uuid4().hex
        self.mock_logger_instance.log_anomaly.return_value = expected_return

        result = self.hub.log_anomaly(
            source=rand_source,
            severity=rand_severity,
            details=rand_details,
            telemetry_snapshot=rand_telemetry
        )

        self.mock_logger_instance.log_anomaly.assert_called_once_with(
            source=rand_source,
            severity=rand_severity,
            details=rand_details,
            telemetry_snapshot=rand_telemetry
        )
        self.assertEqual(result, expected_return)

    def test_aggregate_and_report_proxy(self):
        rand_metric = uuid.uuid4().hex
        rand_value = random.uniform(-1000.0, 1000.0)

        expected_return = {uuid.uuid4().hex: random.randint(1, 100)}
        self.mock_aggregator_instance.aggregate_and_report.return_value = expected_return

        result = self.hub.aggregate_and_report(
            metric_name=rand_metric,
            value=rand_value
        )

        self.mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
            metric_name=rand_metric,
            value=rand_value
        )
        self.assertEqual(result, expected_return)

    def test_generate_final_report_proxy(self):
        expected_report = [uuid.uuid4().hex, uuid.uuid4().hex]
        self.mock_aggregator_instance.generate_final_report.return_value = expected_report

        result = self.hub.generate_final_report()

        self.mock_aggregator_instance.generate_final_report.assert_called_once()
        self.assertEqual(result, expected_report)

if __name__ == "__main__":
    unittest.main()