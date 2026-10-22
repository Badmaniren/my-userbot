import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHub(unittest.TestCase):

    def setUp(self):
        self.random_repo = f"/repo/{uuid.uuid4().hex}"
        self.random_log = f"/logs/{uuid.uuid4().hex}.log"
        self.random_threshold = round(random.uniform(0.1, 99.9), 2)

        with patch("skills.anomaly_audit_hub.AnomalyLogger") as mock_logger_cls, \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator") as mock_aggregator_cls:

            self.mock_logger_instance = mock_logger_cls.return_value
            self.mock_aggregator_instance = mock_aggregator_cls.return_value

            self.hub = AnomalyAuditHub(
                repo_path=self.random_repo,
                log_path=self.random_log,
                threshold=self.random_threshold
            )

    def test_init_initialization(self):
        self.assertEqual(self.hub.logger, self.mock_logger_instance)
        self.assertEqual(self.hub.aggregator, self.mock_aggregator_instance)

    def test_log_anomaly_delegates_correctly(self):
        random_source = ''.join(random.choices(string.ascii_letters, k=10))
        random_severity = random.choice(["INFO", "WARNING", "CRITICAL", "FATAL"])
        random_details = {uuid.uuid4().hex: uuid.uuid4().hex}
        random_telemetry = {uuid.uuid4().hex: random.randint(1, 1000)}

        expected_result = uuid.uuid4().hex
        self.mock_logger_instance.log_anomaly.return_value = expected_result

        result = self.hub.log_anomaly(
            source=random_source,
            severity=random_severity,
            details=random_details,
            telemetry_snapshot=random_telemetry
        )

        self.mock_logger_instance.log_anomaly.assert_called_once_with(
            source=random_source,
            severity=random_severity,
            details=random_details,
            telemetry_snapshot=random_telemetry
        )
        self.assertEqual(result, expected_result)

    def test_aggregate_and_report_delegates_correctly(self):
        random_metric = f"metric_{uuid.uuid4().hex[:6]}"
        random_value = round(random.uniform(-500.0, 500.0), 4)

        expected_aggregation = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_aggregator_instance.aggregate_and_report.return_value = expected_aggregation

        result = self.hub.aggregate_and_report(
            metric_name=random_metric,
            value=random_value
        )

        self.mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
            metric_name=random_metric,
            value=random_value
        )
        self.assertEqual(result, expected_aggregation)

    def test_generate_final_report_delegates_correctly(self):
        expected_report = [uuid.uuid4().hex, uuid.uuid4().hex]
        self.mock_aggregator_instance.generate_final_report.return_value = expected_report

        result = self.hub.generate_final_report()

        self.mock_aggregator_instance.generate_final_report.assert_called_once_with()
        self.assertEqual(result, expected_report)


if __name__ == "__main__":
    unittest.main()