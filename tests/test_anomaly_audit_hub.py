import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHub(unittest.TestCase):

    def setUp(self):
        self.repo_path_val = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.log_path_val = f"/var/log/{uuid.uuid4().hex}.log"
        self.threshold_val = round(random.uniform(1.0, 100.0), 2)

    def test_composition_and_initialization(self):
        with patch('skills.anomaly_audit_hub.AnomalyLogger') as mock_logger_cls, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as mock_aggregator_cls:

            mock_logger_instance = mock_logger_cls.return_value
            mock_aggregator_instance = mock_aggregator_cls.return_value

            hub = AnomalyAuditHub(
                repo_path=self.repo_path_val,
                log_path=self.log_path_val,
                threshold=self.threshold_val
            )

            mock_logger_cls.assert_called_once_with(log_path=self.log_path_val)
            mock_aggregator_cls.assert_called_once_with(
                repo_path=self.repo_path_val,
                log_path=self.log_path_val,
                threshold=self.threshold_val,
                logger=mock_logger_instance
            )
            self.assertEqual(hub.logger, mock_logger_instance)
            self.assertEqual(hub.aggregator, mock_aggregator_instance)

    def test_audit_log_anomaly_delegation(self):
        source_val = ''.join(random.choices(string.ascii_letters, k=10))
        severity_val = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        details_val = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_val = {uuid.uuid4().hex: random.randint(1, 1000)}

        with patch('skills.anomaly_audit_hub.AnomalyLogger') as mock_logger_cls, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator'):

            mock_logger_instance = mock_logger_cls.return_value
            hub = AnomalyAuditHub(
                repo_path=self.repo_path_val,
                log_path=self.log_path_val,
                threshold=self.threshold_val
            )

            hub.log_anomaly(
                source=source_val,
                severity=severity_val,
                details=details_val,
                telemetry_snapshot=telemetry_val
            )

            mock_logger_instance.log_anomaly.assert_called_once_with(
                source=source_val,
                severity=severity_val,
                details=details_val,
                telemetry_snapshot=telemetry_val
            )

    def test_audit_aggregate_and_report_delegation(self):
        metric_name_val = f"metric_{uuid.uuid4().hex[:6]}"
        value_val = random.uniform(0.0, 500.0)
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.anomaly_audit_hub.AnomalyLogger'), \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as mock_aggregator_cls:

            mock_aggregator_instance = mock_aggregator_cls.return_value
            mock_aggregator_instance.aggregate_and_report.return_value = expected_result

            hub = AnomalyAuditHub(
                repo_path=self.repo_path_val,
                log_path=self.log_path_val,
                threshold=self.threshold_val
            )

            result = hub.aggregate_and_report(metric_name=metric_name_val, value=value_val)

            mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
                metric_name=metric_name_val,
                value=value_val
            )
            self.assertEqual(result, expected_result)

    def test_audit_generate_final_report_delegation(self):
        expected_report = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "status": random.choice(["SECURE", "VULNERABLE", "WARNING"])
        }

        with patch('skills.anomaly_audit_hub.AnomalyLogger'), \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as mock_aggregator_cls:

            mock_aggregator_instance = mock_aggregator_cls.return_value
            mock_aggregator_instance.generate_final_report.return_value = expected_report

            hub = AnomalyAuditHub(
                repo_path=self.repo_path_val,
                log_path=self.log_path_val,
                threshold=self.threshold_val
            )

            report = hub.generate_final_report()

            mock_aggregator_instance.generate_final_report.assert_called_once()
            self.assertEqual(report, expected_report)


if __name__ == '__main__':
    unittest.main()