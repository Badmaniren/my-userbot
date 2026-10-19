import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHub(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.log_path = f"/tmp/log_{uuid.uuid4().hex}.log"
        self.threshold = round(random.uniform(0.1, 99.9), 4)
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def test_init_sets_components(self):
        self.assertEqual(self.hub.logger.log_path, self.log_path)
        self.assertEqual(self.hub.aggregator.repo_path, self.repo_path)
        self.assertEqual(self.hub.aggregator.log_path, self.log_path)
        self.assertEqual(self.hub.aggregator.threshold, self.threshold)
        self.assertEqual(self.hub.aggregator.logger, self.hub.logger)

    def test_log_anomaly_delegates_correctly(self):
        source_val = ''.join(random.choices(string.ascii_lowercase, k=10))
        severity_val = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_val = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}
        telemetry_val = {uuid.uuid4().hex: random.random() for _ in range(3)}
        expected_return = uuid.uuid4().hex

        with patch.object(self.hub.logger, 'log_anomaly', return_value=expected_return) as mock_log:
            result = self.hub.log_anomaly(
                source=source_val,
                severity=severity_val,
                details=details_val,
                telemetry_snapshot=telemetry_val
            )
            mock_log.assert_called_once_with(
                source=source_val,
                severity=severity_val,
                details=details_val,
                telemetry_snapshot=telemetry_val
            )
            self.assertEqual(result, expected_return)

    def test_aggregate_and_report_delegates_correctly(self):
        metric_name_val = ''.join(random.choices(string.ascii_lowercase, k=8))
        value_val = round(random.uniform(-100.0, 100.0), 2)
        expected_return = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch.object(self.hub.aggregator, 'aggregate_and_report', return_value=expected_return) as mock_agg:
            result = self.hub.aggregate_and_report(
                metric_name=metric_name_val,
                value=value_val
            )
            mock_agg.assert_called_once_with(
                metric_name=metric_name_val,
                value=value_val
            )
            self.assertEqual(result, expected_return)

    def test_generate_final_report_delegates_correctly(self):
        expected_return = [uuid.uuid4().hex, uuid.uuid4().hex]

        with patch.object(self.hub.aggregator, 'generate_final_report', return_value=expected_return) as mock_gen:
            result = self.hub.generate_final_report()
            mock_gen.assert_called_once()
            self.assertEqual(result, expected_return)

if __name__ == '__main__':
    unittest.main()