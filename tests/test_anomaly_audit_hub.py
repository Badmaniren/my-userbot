import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHub(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/var/log/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 0.99)

    def test_initialization_and_delegation(self):
        with patch('skills.anomaly_audit_hub.AnomalyLogger') as MockLogger, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as MockAggregator:

            mock_logger_instance = MockLogger.return_value
            mock_aggregator_instance = MockAggregator.return_value

            hub = AnomalyAuditHub(self.repo_path, self.log_path, self.threshold)

            MockLogger.assert_called_once_with(log_path=self.log_path)
            MockAggregator.assert_called_once_with(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold,
                logger=mock_logger_instance
            )

    def test_log_anomaly_integration(self):
        with patch('skills.anomaly_audit_hub.AnomalyLogger') as MockLogger, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator'):

            mock_logger_instance = MockLogger.return_value
            hub = AnomalyAuditHub(self.repo_path, self.log_path, self.threshold)

            source = uuid.uuid4().hex
            severity = random.choice(['CRITICAL', 'WARNING', 'INFO'])
            details = {uuid.uuid4().hex: random.randint(1, 100)}
            telemetry = {uuid.uuid4().hex: random.random()}

            expected_result = uuid.uuid4().hex
            mock_logger_instance.log_anomaly.return_value = expected_result

            result = hub.log_anomaly(source, severity, details, telemetry)

            mock_logger_instance.log_anomaly.assert_called_once_with(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry
            )
            self.assertEqual(result, expected_result)

    def test_aggregate_and_report_integration(self):
        with patch('skills.anomaly_audit_hub.AnomalyLogger'), \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as MockAggregator:

            mock_aggregator_instance = MockAggregator.return_value
            hub = AnomalyAuditHub(self.repo_path, self.log_path, self.threshold)

            metric_name = uuid.uuid4().hex
            value = random.uniform(0.0, 1000.0)
            expected_report = {uuid.uuid4().hex: random.random()}

            mock_aggregator_instance.aggregate_and_report.return_value = expected_report

            result = hub.aggregate_and_report(metric_name, value)

            mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
                metric_name=metric_name,
                value=value
            )
            self.assertEqual(result, expected_report)

    def test_generate_final_report_integration(self):
        with patch('skills.anomaly_audit_hub.AnomalyLogger'), \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as MockAggregator:

            mock_aggregator_instance = MockAggregator.return_value
            hub = AnomalyAuditHub(self.repo_path, self.log_path, self.threshold)

            final_data = {uuid.uuid4().hex: uuid.uuid4().hex}
            mock_aggregator_instance.generate_final_report.return_value = final_data

            result = hub.generate_final_report()

            mock_aggregator_instance.generate_final_report.assert_called_once()
            self.assertEqual(result, final_data)

if __name__ == '__main__':
    unittest.main()