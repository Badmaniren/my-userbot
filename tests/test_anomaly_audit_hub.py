import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHub(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 99.9)

    def test_init_and_signatures(self):
        with patch('skills.anomaly_audit_hub.AnomalyLogger') as mock_logger_cls, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as mock_aggregator_cls:

            mock_logger_instance = mock_logger_cls.return_value
            mock_aggregator_instance = mock_aggregator_cls.return_value

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
                logger=mock_logger_instance
            )
            self.assertEqual(hub.logger, mock_logger_instance)
            self.assertEqual(hub.aggregator, mock_aggregator_instance)

    def test_log_anomaly_delegation(self):
        source_val = f"source_{uuid.uuid4().hex[:6]}"
        severity_val = random.choice(["INFO", "WARNING", "CRITICAL", "ERROR"])
        details_val = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}
        telemetry_val = {uuid.uuid4().hex: random.random() for _ in range(2)}
        expected_result = uuid.uuid4().hex

        with patch('skills.anomaly_audit_hub.AnomalyLogger') as mock_logger_cls, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator'):

            mock_logger_instance = mock_logger_cls.return_value
            mock_logger_instance.log_anomaly.return_value = expected_result

            hub = AnomalyAuditHub(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

            res = hub.log_anomaly(
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
            self.assertEqual(res, expected_result)

    def test_aggregate_and_report_delegation(self):
        metric_name_val = f"metric_{uuid.uuid4().hex[:6]}"
        value_val = random.uniform(-1000.0, 1000.0)
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.anomaly_audit_hub.AnomalyLogger'), \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as mock_aggregator_cls:

            mock_aggregator_instance = mock_aggregator_cls.return_value
            mock_aggregator_instance.aggregate_and_report.return_value = expected_result

            hub = AnomalyAuditHub(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

            res = hub.aggregate_and_report(
                metric_name=metric_name_val,
                value=value_val
            )

            mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
                metric_name=metric_name_val,
                value=value_val
            )
            self.assertEqual(res, expected_result)

    def test_generate_final_report_delegation(self):
        expected_result = f"report_{uuid.uuid4().hex}"

        with patch('skills.anomaly_audit_hub.AnomalyLogger'), \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as mock_aggregator_cls:

            mock_aggregator_instance = mock_aggregator_cls.return_value
            mock_aggregator_instance.generate_final_report.return_value = expected_result

            hub = AnomalyAuditHub(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

            res = hub.generate_final_report()

            mock_aggregator_instance.generate_final_report.assert_called_once()
            self.assertEqual(res, expected_result)

if __name__ == '__main__':
    unittest.main()