import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_report_aggregator import AnomalyReportAggregatorError


class TestAnomalyAuditHub(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/repo/{uuid.uuid4().hex}"
        self.random_log_path = f"/logs/{uuid.uuid4().hex}.log"
        self.random_threshold = round(random.uniform(0.1, 99.9), 2)

        self.hub = AnomalyAuditHub(
            repo_path=self.random_repo_path,
            log_path=self.random_log_path,
            threshold=self.random_threshold
        )

    def test_init_sets_correct_dependencies(self):
        self.assertEqual(self.hub.aggregator.repo_path, self.random_repo_path)
        self.assertEqual(self.hub.aggregator.threshold, self.random_threshold)
        self.assertEqual(self.hub.logger.log_path, self.random_log_path)

    def test_log_anomaly_delegates_to_logger(self):
        random_source = ''.join(random.choices(string.ascii_letters, k=10))
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        random_details = {uuid.uuid4().hex: uuid.uuid4().hex}
        random_telemetry = {uuid.uuid4().hex: random.randint(1, 100)}
        expected_result = uuid.uuid4().hex

        with patch.object(self.hub.logger, 'log_anomaly', return_value=expected_result) as mock_log:
            result = self.hub.log_anomaly(
                source=random_source,
                severity=random_severity,
                details=random_details,
                telemetry_snapshot=random_telemetry
            )
            mock_log.assert_called_once_with(
                source=random_source,
                severity=random_severity,
                details=random_details,
                telemetry_snapshot=random_telemetry
            )
            self.assertEqual(result, expected_result)

    def test_aggregate_and_report_delegates_to_aggregator(self):
        random_metric = ''.join(random.choices(string.ascii_lowercase, k=8))
        random_value = round(random.uniform(1.0, 1000.0), 2)
        expected_report_snippet = uuid.uuid4().hex

        with patch.object(self.hub.aggregator, 'aggregate_and_report', return_value=expected_report_snippet) as mock_agg:
            result = self.hub.aggregate_and_report(
                metric_name=random_metric,
                value=random_value
            )
            mock_agg.assert_called_once_with(
                metric_name=random_metric,
                value=random_value
            )
            self.assertEqual(result, expected_report_snippet)

    def test_generate_final_report_delegates_to_aggregator(self):
        expected_final_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.hub.aggregator, 'generate_final_report', return_value=expected_final_data) as mock_gen:
            result = self.hub.generate_final_report()
            mock_gen.assert_called_once()
            self.assertEqual(result, expected_final_data)

    def test_aggregate_and_report_raises_custom_exception_without_swallowing(self):
        random_metric = ''.join(random.choices(string.ascii_lowercase, k=6))
        random_value = round(random.uniform(0.0, 50.0), 2)
        random_error_msg = uuid.uuid4().hex

        with patch.object(self.hub.aggregator, 'aggregate_and_report', side_effect=AnomalyReportAggregatorError(random_error_msg)):
            with self.assertRaises(AnomalyReportAggregatorError) as ctx:
                self.hub.aggregate_and_report(metric_name=random_metric, value=random_value)
            self.assertIn(random_error_msg, str(ctx.exception))


if __name__ == '__main__':
    unittest.main()