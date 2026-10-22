import unittest
from unittest.mock import patch
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHub(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/var/repos/{uuid.uuid4().hex}"
        self.random_log_path = f"/var/logs/{uuid.uuid4().hex}.log"
        self.random_threshold = round(random.uniform(0.1, 99.9), 2)

    @patch('skills.anomaly_audit_hub.AnomalyReportAggregator')
    @patch('skills.anomaly_audit_hub.AnomalyLogger')
    def test_init_establishes_dependencies(self, mock_logger_class, mock_aggregator_class):
        instance = AnomalyAuditHub(
            repo_path=self.random_repo_path,
            log_path=self.random_log_path,
            threshold=self.random_threshold
        )

        mock_logger_class.assert_called_once_with(log_path=self.random_log_path)
        mock_aggregator_class.assert_called_once_with(
            repo_path=self.random_repo_path,
            log_path=self.random_log_path,
            threshold=self.random_threshold,
            logger=instance.logger
        )

    def test_log_anomaly_delegates_to_logger(self):
        random_source = ''.join(random.choices(string.ascii_letters, k=10))
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        random_details = {uuid.uuid4().hex: uuid.uuid4().hex}
        random_snapshot = {uuid.uuid4().hex: random.randint(1, 1000)}
        expected_return_value = uuid.uuid4().hex

        with patch('skills.anomaly_audit_hub.AnomalyLogger') as mock_logger_class, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator'):

            mock_logger_instance = mock_logger_class.return_value
            mock_logger_instance.log_anomaly.return_value = expected_return_value

            hub = AnomalyAuditHub(
                repo_path=self.random_repo_path,
                log_path=self.random_log_path,
                threshold=self.random_threshold
            )

            result = hub.log_anomaly(
                source=random_source,
                severity=random_severity,
                details=random_details,
                telemetry_snapshot=random_snapshot
            )

            mock_logger_instance.log_anomaly.assert_called_once_with(
                source=random_source,
                severity=random_severity,
                details=random_details,
                telemetry_snapshot=random_snapshot
            )
            self.assertEqual(result, expected_return_value)

    def test_aggregate_and_report_delegates_to_aggregator(self):
        random_metric_name = uuid.uuid4().hex
        random_value = round(random.uniform(-500.0, 500.0), 3)
        expected_return_value = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.anomaly_audit_hub.AnomalyLogger'), \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as mock_aggregator_class:

            mock_aggregator_instance = mock_aggregator_class.return_value
            mock_aggregator_instance.aggregate_and_report.return_value = expected_return_value

            hub = AnomalyAuditHub(
                repo_path=self.random_repo_path,
                log_path=self.random_log_path,
                threshold=self.random_threshold
            )

            result = hub.aggregate_and_report(
                metric_name=random_metric_name,
                value=random_value
            )

            mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
                random_metric_name,
                random_value
            )
            self.assertEqual(result, expected_return_value)

    def test_generate_final_report_delegates_to_aggregator(self):
        expected_return_value = [uuid.uuid4().hex, uuid.uuid4().hex]

        with patch('skills.anomaly_audit_hub.AnomalyLogger'), \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as mock_aggregator_class:

            mock_aggregator_instance = mock_aggregator_class.return_value
            mock_aggregator_instance.generate_final_report.return_value = expected_return_value

            hub = AnomalyAuditHub(
                repo_path=self.random_repo_path,
                log_path=self.random_log_path,
                threshold=self.random_threshold
            )

            result = hub.generate_final_report()

            mock_aggregator_instance.generate_final_report.assert_called_once()
            self.assertEqual(result, expected_return_value)

if __name__ == '__main__':
    unittest.main()