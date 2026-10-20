import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_report_aggregator import AnomalyReportAggregatorError

class TestAnomalyAuditHub(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/var/log/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 0.99)
        self.hub = AnomalyAuditHub(self.repo_path, self.log_path, self.threshold)

    def test_log_anomaly_propagation(self):
        source = uuid.uuid4().hex
        severity = random.choice(["CRITICAL", "WARNING", "INFO"])
        details = {"key": uuid.uuid4().hex}
        telemetry = {"cpu": random.random()}

        with patch.object(self.hub.logger, 'log_anomaly') as mock_log:
            expected_result = uuid.uuid4().hex
            mock_log.return_value = expected_result

            result = self.hub.log_anomaly(source, severity, details, telemetry)

            self.assertEqual(result, expected_result)
            mock_log.assert_called_once_with(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry
            )

    def test_aggregate_and_report_success(self):
        metric = uuid.uuid4().hex
        value = random.uniform(0, 100)
        expected_output = {"status": "processed", "id": uuid.uuid4().hex}

        with patch.object(self.hub.aggregator, 'aggregate_and_report') as mock_agg:
            mock_agg.return_value = expected_output

            result = self.hub.aggregate_and_report(metric, value)

            self.assertEqual(result, expected_output)
            mock_agg.assert_called_once_with(metric_name=metric, value=value)

    def test_aggregate_and_report_exception_handling(self):
        metric = uuid.uuid4().hex
        value = random.uniform(0, 100)
        error_msg = uuid.uuid4().hex

        with patch.object(self.hub.aggregator, 'aggregate_and_report') as mock_agg:
            mock_agg.side_effect = AnomalyReportAggregatorError(error_msg)

            with self.assertRaises(AnomalyReportAggregatorError) as cm:
                self.hub.aggregate_and_report(metric, value)

            self.assertEqual(str(cm.exception), error_msg)

    def test_generate_final_report_integrity(self):
        mock_report = {
            "summary": uuid.uuid4().hex,
            "score": random.random()
        }

        with patch.object(self.hub.aggregator, 'generate_final_report') as mock_gen:
            mock_gen.return_value = mock_report

            result = self.hub.generate_final_report()

            self.assertEqual(result, mock_report)
            mock_gen.assert_called_once()

    def test_initialization_parameters(self):
        self.assertEqual(self.hub.aggregator.repo_path, self.repo_path)
        self.assertEqual(self.hub.aggregator.threshold, self.threshold)
        self.assertEqual(self.hub.logger.log_path, self.log_path)

if __name__ == '__main__':
    unittest.main()