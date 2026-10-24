import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHub(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/var/repo/{uuid.uuid4().hex}"
        self.log_path = f"/var/log/{uuid.uuid4().hex}.log"
        self.threshold = round(random.uniform(0.1, 99.9), 4)

    @patch('skills.anomaly_audit_hub.AnomalyReportAggregator')
    @patch('skills.anomaly_audit_hub.AnomalyLogger')
    def test_init_initialization(self, mock_logger_class, mock_aggregator_class):
        mock_logger_instance = mock_logger_class.return_value
        mock_aggregator_instance = mock_aggregator_class.return_value

        hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        mock_logger_class.assert_called_once_with(log_path=self.log_path)
        mock_aggregator_class.assert_called_once_with(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold,
            logger=mock_logger_instance
        )
        self.assertEqual(hub.logger, mock_logger_instance)
        self.assertEqual(hub.aggregator, mock_aggregator_instance)

    @patch('skills.anomaly_audit_hub.AnomalyReportAggregator')
    @patch('skills.anomaly_audit_hub.AnomalyLogger')
    def test_log_anomaly_delegation(self, mock_logger_class, mock_aggregator_class):
        mock_logger_instance = mock_logger_class.return_value
        expected_return = uuid.uuid4().hex
        mock_logger_instance.log_anomaly.return_value = expected_return

        hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        source = ''.join(random.choices(string.ascii_lowercase, k=10))
        severity = ''.join(random.choices(string.ascii_uppercase, k=5))
        details = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_snapshot = {uuid.uuid4().hex: random.random()}

        result = hub.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        mock_logger_instance.log_anomaly.assert_called_once_with(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        self.assertEqual(result, expected_return)

    @patch('skills.anomaly_audit_hub.AnomalyReportAggregator')
    @patch('skills.anomaly_audit_hub.AnomalyLogger')
    def test_aggregate_and_report_delegation(self, mock_logger_class, mock_aggregator_class):
        mock_aggregator_instance = mock_aggregator_class.return_value
        expected_return = {uuid.uuid4().hex: random.randint(1, 100)}
        mock_aggregator_instance.aggregate_and_report.return_value = expected_return

        hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        metric_name = uuid.uuid4().hex
        value = round(random.uniform(1.0, 500.0), 2)

        result = hub.aggregate_and_report(
            metric_name=metric_name,
            value=value
        )

        mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
            metric_name=metric_name,
            value=value
        )
        self.assertEqual(result, expected_return)

    @patch('skills.anomaly_audit_hub.AnomalyReportAggregator')
    @patch('skills.anomaly_audit_hub.AnomalyLogger')
    def test_generate_final_report_delegation(self, mock_logger_class, mock_aggregator_class):
        mock_aggregator_instance = mock_aggregator_class.return_value
        expected_return = uuid.uuid4().hex
        mock_aggregator_instance.generate_final_report.return_value = expected_return

        hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        result = hub.generate_final_report()

        mock_aggregator_instance.generate_final_report.assert_called_once()
        self.assertEqual(result, expected_return)

if __name__ == '__main__':
    unittest.main()