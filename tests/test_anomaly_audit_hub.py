import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHub(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.log_path = f"/logs/{uuid.uuid4().hex}.log"
        self.threshold = round(random.uniform(0.1, 99.9), 2)

    @patch("skills.anomaly_audit_hub.AnomalyLogger")
    @patch("skills.anomaly_audit_hub.AnomalyReportAggregator")
    def test_init_instantiates_dependencies(self, mock_aggregator_class, mock_logger_class):
        instance = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

        mock_logger_class.assert_called_once_with(log_path=self.log_path)
        mock_aggregator_class.assert_called_once_with(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold,
            logger=instance.logger
        )

    @patch("skills.anomaly_audit_hub.AnomalyReportAggregator")
    @patch("skills.anomaly_audit_hub.AnomalyLogger")
    def test_log_anomaly_delegates_to_logger(self, mock_logger_class, mock_aggregator_class):
        mock_logger_instance = mock_logger_class.return_value
        expected_return = {'status': uuid.uuid4().hex}
        mock_logger_instance.log_anomaly.return_value = expected_return

        source = ''.join(random.choices(string.ascii_lowercase, k=10))
        severity = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        details = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_snapshot = {uuid.uuid4().hex: random.random()}

        hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
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

    @patch("skills.anomaly_audit_hub.AnomalyReportAggregator")
    @patch("skills.anomaly_audit_hub.AnomalyLogger")
    def test_aggregate_and_report_delegates_to_aggregator(self, mock_logger_class, mock_aggregator_class):
        mock_aggregator_instance = mock_aggregator_class.return_value
        expected_report = {uuid.uuid4().hex: random.randint(1, 100)}
        mock_aggregator_instance.aggregate_and_report.return_value = expected_report

        metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        value = round(random.uniform(1.0, 1000.0), 3)

        hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        result = hub.aggregate_and_report(metric_name=metric_name, value=value)

        mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
            metric_name=metric_name,
            value=value
        )
        self.assertEqual(result, expected_report)

    @patch("skills.anomaly_audit_hub.AnomalyReportAggregator")
    @patch("skills.anomaly_audit_hub.AnomalyLogger")
    def test_generate_final_report_delegates_to_aggregator(self, mock_logger_class, mock_aggregator_class):
        mock_aggregator_instance = mock_aggregator_class.return_value
        expected_final_report = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            'metric_threshold': self.threshold
        }
        mock_aggregator_instance.generate_final_report.return_value = expected_final_report

        hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        result = hub.generate_final_report()

        mock_aggregator_instance.generate_final_report.assert_called_once_with()
        self.assertEqual(result, expected_final_report)


if __name__ == '__main__':
    unittest.main()