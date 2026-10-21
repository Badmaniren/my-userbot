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
        self.threshold = round(random.uniform(0.1, 99.9), 2)

        self.source_name = f"source_{uuid.uuid4().hex[:8]}"
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.metric_value = round(random.uniform(1.0, 1000.0), 2)

        self.details = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}
        self.telemetry = {uuid.uuid4().hex: random.randint(0, 100) for _ in range(2)}

    @patch("skills.anomaly_audit_hub.AnomalyLogger")
    @patch("skills.anomaly_audit_hub.AnomalyReportAggregator")
    def test_init_initializes_submodules(self, mock_aggregator_cls, mock_logger_cls):
        hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        mock_logger_cls.assert_called_once_with(log_path=self.log_path)
        mock_aggregator_cls.assert_called_once_with(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold,
            logger=hub.logger
        )

    @patch("skills.anomaly_audit_hub.AnomalyLogger")
    @patch("skills.anomaly_audit_hub.AnomalyReportAggregator")
    def test_log_anomaly_delegates_to_logger(self, mock_aggregator_cls, mock_logger_cls):
        mock_logger_instance = mock_logger_cls.return_value
        expected_return_value = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_logger_instance.log_anomaly.return_value = expected_return_value

        hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        result = hub.log_anomaly(
            source=self.source_name,
            severity=self.severity_level,
            details=self.details,
            telemetry_snapshot=self.telemetry
        )

        mock_logger_instance.log_anomaly.assert_called_once_with(
            source=self.source_name,
            severity=self.severity_level,
            details=self.details,
            telemetry_snapshot=self.telemetry
        )
        self.assertEqual(result, expected_return_value)

    @patch("skills.anomaly_audit_hub.AnomalyLogger")
    @patch("skills.anomaly_audit_hub.AnomalyReportAggregator")
    def test_aggregate_and_report_delegates_to_aggregator(self, mock_aggregator_cls, mock_logger_cls):
        mock_aggregator_instance = mock_aggregator_cls.return_value
        expected_aggregation = {uuid.uuid4().hex: random.random()}
        mock_aggregator_instance.aggregate_and_report.return_value = expected_aggregation

        hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        result = hub.aggregate_and_report(
            metric_name=self.metric_name,
            value=self.metric_value
        )

        mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
            metric_name=self.metric_name,
            value=self.metric_value
        )
        self.assertEqual(result, expected_aggregation)

    @patch("skills.anomaly_audit_hub.AnomalyLogger")
    @patch("skills.anomaly_audit_hub.AnomalyReportAggregator")
    def test_generate_final_report_delegates_to_aggregator(self, mock_aggregator_cls, mock_logger_cls):
        mock_aggregator_instance = mock_aggregator_cls.return_value
        expected_report = f"Report_{uuid.uuid4().hex}"
        mock_aggregator_instance.generate_final_report.return_value = expected_report

        hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        result = hub.generate_final_report()

        mock_aggregator_instance.generate_final_report.assert_called_once()
        self.assertEqual(result, expected_report)


if __name__ == "__main__":
    unittest.main()