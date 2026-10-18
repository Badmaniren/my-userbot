import unittest
from unittest.mock import patch
import uuid
import random
import io
import string

from skills.anomaly_security_hub import AnomalySecurityHub
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger


class TestAnomalySecurityHub(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(1.0, 10.0)

        self.source = ''.join(random.choices(string.ascii_letters, k=8))
        self.severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.details = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}
        self.telemetry_snapshot = {uuid.uuid4().hex: random.random() for _ in range(2)}

        self.metric_name = uuid.uuid4().hex
        self.metric_value = random.uniform(0.0, 100.0)

    def test_initialization_composes_modules(self):
        with patch('skills.anomaly_security_hub.AnomalyAuditHub') as mock_audit_cls, \
             patch('skills.anomaly_security_hub.AnomalyLogger') as mock_logger_cls:

            mock_audit_instance = mock_audit_cls.return_value
            mock_logger_instance = mock_logger_cls.return_value

            hub = AnomalySecurityHub(repo_path=self.repo_path, log_path=self.log_path, threshold=self.threshold)

            mock_audit_cls.assert_called_once_with(repo_path=self.repo_path, log_path=self.log_path, threshold=self.threshold)
            mock_logger_cls.assert_called_once_with(log_path=self.log_path)

            self.assertEqual(hub.audit_hub, mock_audit_instance)
            self.assertEqual(hub.logger, mock_logger_instance)

    def test_log_anomaly_delegates_to_both(self):
        hub = AnomalySecurityHub(repo_path=self.repo_path, log_path=self.log_path, threshold=self.threshold)

        with patch.object(hub.audit_hub, 'log_anomaly') as mock_audit_log, \
             patch.object(hub.logger, 'log_anomaly') as mock_logger_log:

            hub.log_anomaly(
                source=self.source,
                severity=self.severity,
                details=self.details,
                telemetry_snapshot=self.telemetry_snapshot
            )

            mock_audit_log.assert_called_once_with(
                source=self.source,
                severity=self.severity,
                details=self.details,
                telemetry_snapshot=self.telemetry_snapshot
            )
            mock_logger_log.assert_called_once_with(
                source=self.source,
                severity=self.severity,
                details=self.details,
                telemetry_snapshot=self.telemetry_snapshot
            )

    def test_aggregate_and_report_delegates_correctly(self):
        hub = AnomalySecurityHub(repo_path=self.repo_path, log_path=self.log_path, threshold=self.threshold)
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(hub.audit_hub, 'aggregate_and_report', return_value=expected_result) as mock_aggregate:
            result = hub.aggregate_and_report(metric_name=self.metric_name, value=self.metric_value)

            mock_aggregate.assert_called_once_with(metric_name=self.metric_name, value=self.metric_value)
            self.assertEqual(result, expected_result)

    def test_generate_final_report_delegates_and_enriches(self):
        hub = AnomalySecurityHub(repo_path=self.repo_path, log_path=self.log_path, threshold=self.threshold)
        audit_report = {uuid.uuid4().hex: uuid.uuid4().hex}
        logger_report = [uuid.uuid4().hex, uuid.uuid4().hex]

        with patch.object(hub.audit_hub, 'generate_final_report', return_value=audit_report) as mock_gen_audit, \
             patch.object(hub.logger, 'get_structured_report', return_value=logger_report) as mock_get_logger:

            report = hub.generate_final_report()

            mock_gen_audit.assert_called_once()
            mock_get_logger.assert_called_once()

            self.assertIn("audit_report", report)
            self.assertIn("logger_report", report)
            self.assertEqual(report["audit_report"], audit_report)
            self.assertEqual(report["logger_report"], logger_report)


if __name__ == '__main__':
    unittest.main()