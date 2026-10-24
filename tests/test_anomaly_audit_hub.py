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

    @patch('skills.anomaly_audit_hub.AnomalyReportAggregator')
    @patch('skills.anomaly_audit_hub.AnomalyLogger')
    def test_init_sets_dependencies_correctly(self, mock_logger_cls, mock_aggregator_cls):
        instance = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_path, threshold=self.threshold)

        mock_logger_cls.assert_called_once_with(log_path=self.log_path)
        mock_aggregator_cls.assert_called_once_with(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold,
            logger=instance.logger
        )

    @patch('skills.anomaly_audit_hub.AnomalyReportAggregator')
    @patch('skills.anomaly_audit_hub.AnomalyLogger')
    def test_log_anomaly_delegates_to_logger(self, mock_logger_cls, mock_aggregator_cls):
        mock_logger_instance = mock_logger_cls.return_value
        expected_result = f"logged_{uuid.uuid4().hex}"
        mock_logger_instance.log_anomaly.return_value = expected_result

        source = ''.join(random.choices(string.ascii_letters, k=10))
        severity = random.choice(["INFO", "WARNING", "CRITICAL", "ERROR"])
        details = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry = {uuid.uuid4().hex: random.random()}

        hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_path, threshold=self.threshold)
        result = hub.log_anomaly(source=source, severity=severity, details=details, telemetry_snapshot=telemetry)

        mock_logger_instance.log_anomaly.assert_called_once_with(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry
        )
        self.assertEqual(result, expected_result)

    @patch('skills.anomaly_audit_hub.AnomalyReportAggregator')
    @patch('skills.anomaly_audit_hub.AnomalyLogger')
    def test_aggregate_and_report_delegates_to_aggregator(self, mock_logger_cls, mock_aggregator_cls):
        mock_aggregator_instance = mock_aggregator_cls.return_value
        expected_result = f"aggregated_{uuid.uuid4().hex}"
        mock_aggregator_instance.aggregate_and_report.return_value = expected_result

        metric_name = f"metric_{uuid.uuid4().hex}"
        value = round(random.uniform(-1000, 1000), 4)

        hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_path, threshold=self.threshold)
        result = hub.aggregate_and_report(metric_name=metric_name, value=value)

        mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
            metric_name=metric_name,
            value=value
        )
        self.assertEqual(result, expected_result)

    @patch('skills.anomaly_audit_hub.AnomalyReportAggregator')
    @patch('skills.anomaly_audit_hub.AnomalyLogger')
    def test_generate_final_report_delegates_to_aggregator(self, mock_logger_cls, mock_aggregator_cls):
        mock_aggregator_instance = mock_aggregator_cls.return_value
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_aggregator_instance.generate_final_report.return_value = expected_result

        hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_path, threshold=self.threshold)
        result = hub.generate_final_report()

        mock_aggregator_instance.generate_final_report.assert_called_once()
        self.assertEqual(result, expected_result)


if __name__ == '__main__':
    unittest.main()