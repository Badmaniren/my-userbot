import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_report_aggregator import AnomalyReportAggregator

class TestAnomalyAuditHub(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 1.0)

        with patch('skills.anomaly_logger.AnomalyLogger'), \
             patch('skills.anomaly_report_aggregator.AnomalyReportAggregator'):
            self.hub = AnomalyAuditHub(self.repo_path, self.log_path, self.threshold)

    def test_log_anomaly_propagation(self):
        source = uuid.uuid4().hex
        severity = random.choice(['CRITICAL', 'WARNING', 'INFO'])
        details = {uuid.uuid4().hex: random.randint(1, 100)}
        telemetry = {uuid.uuid4().hex: random.random()}

        with patch.object(self.hub.logger, 'log_anomaly') as mock_log:
            mock_log.return_value = True
            result = self.hub.log_anomaly(source, severity, details, telemetry)

            mock_log.assert_called_once_with(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry
            )
            self.assertTrue(result)

    def test_log_anomaly_exception_propagation(self):
        source = uuid.uuid4().hex
        severity = "FATAL"
        details = {"error": "trigger"}
        telemetry = {"data": 0}

        with patch.object(self.hub.logger, 'log_anomaly', side_effect=RuntimeError("Audit Failure")):
            with self.assertRaises(RuntimeError) as cm:
                self.hub.log_anomaly(source, severity, details, telemetry)
            self.assertEqual(str(cm.exception), "Audit Failure")

    def test_aggregate_and_report_logic(self):
        metric = uuid.uuid4().hex
        value = random.uniform(0, 1000)
        expected_result = {"status": uuid.uuid4().hex}

        with patch.object(self.hub.aggregator, 'aggregate_and_report') as mock_agg:
            mock_agg.return_value = expected_result
            result = self.hub.aggregate_and_report(metric, value)

            mock_agg.assert_called_once_with(metric_name=metric, value=value)
            self.assertEqual(result, expected_result)

    def test_aggregate_and_report_exception_propagation(self):
        metric = uuid.uuid4().hex
        value = random.random()

        with patch.object(self.hub.aggregator, 'aggregate_and_report', side_effect=ValueError("Aggregation Error")):
            with self.assertRaises(ValueError):
                self.hub.aggregate_and_report(metric, value)

    def test_generate_final_report_integrity(self):
        report_data = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}

        with patch.object(self.hub.aggregator, 'generate_final_report') as mock_gen:
            mock_gen.return_value = report_data
            result = self.hub.generate_final_report()

            mock_gen.assert_called_once()
            self.assertEqual(result, report_data)

    def test_generate_final_report_failure(self):
        with patch.object(self.hub.aggregator, 'generate_final_report', side_effect=ConnectionError("Report Generation Failed")):
            with self.assertRaises(ConnectionError):
                self.hub.generate_final_report()

if __name__ == '__main__':
    unittest.main()