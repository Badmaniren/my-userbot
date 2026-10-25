import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHub(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/{uuid.uuid4().hex}"
        self.rand_log = f"/tmp/{uuid.uuid4().hex}.log"
        self.rand_threshold = random.uniform(0.1, 99.9)
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

    def test_init_sets_attributes_correctly(self):
        self.assertEqual(self.audit_hub.aggregator.repo_path, self.rand_repo)
        self.assertEqual(self.audit_hub.aggregator.log_path, self.rand_log)
        self.assertEqual(self.audit_hub.aggregator.threshold, self.rand_threshold)
        self.assertEqual(self.audit_hub.logger.log_path, self.rand_log)

    def test_log_anomaly_success(self):
        rand_source = uuid.uuid4().hex
        rand_severity = random.choice(["INFO", "WARN", "CRITICAL", "FATAL"])
        rand_details = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_telemetry = {uuid.uuid4().hex: random.random()}
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.audit_hub.logger, 'log_anomaly', return_value=expected_result) as mock_log:
            res = self.audit_hub.log_anomaly(
                source=rand_source,
                severity=rand_severity,
                details=rand_details,
                telemetry_snapshot=rand_telemetry
            )
            mock_log.assert_called_once_with(
                source=rand_source,
                severity=rand_severity,
                details=rand_details,
                telemetry_snapshot=rand_telemetry
            )
            self.assertEqual(res, expected_result)

    def test_log_anomaly_returns_empty_dict_on_none(self):
        rand_source = uuid.uuid4().hex
        rand_severity = uuid.uuid4().hex
        rand_details = {}
        rand_telemetry = {}

        with patch.object(self.audit_hub.logger, 'log_anomaly', return_value=None):
            res = self.audit_hub.log_anomaly(
                source=rand_source,
                severity=rand_severity,
                details=rand_details,
                telemetry_snapshot=rand_telemetry
            )
            self.assertEqual(res, {})

    def test_aggregate_and_report_delegates(self):
        rand_metric = uuid.uuid4().hex
        rand_value = random.uniform(-1000.0, 1000.0)
        expected_aggregation = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch.object(self.audit_hub.aggregator, 'aggregate_and_report', return_value=expected_aggregation) as mock_agg:
            res = self.audit_hub.aggregate_and_report(metric_name=rand_metric, value=rand_value)
            mock_agg.assert_called_once_with(metric_name=rand_metric, value=rand_value)
            self.assertEqual(res, expected_aggregation)

    def test_aggregate_and_report_raises_without_suppression(self):
        rand_metric = uuid.uuid4().hex
        rand_value = random.uniform(0.0, 50.0)
        rand_exception_msg = uuid.uuid4().hex

        with patch.object(self.audit_hub.aggregator, 'aggregate_and_report', side_effect=AttributeError(rand_exception_msg)):
            with self.assertRaises(AttributeError) as ctx:
                self.audit_hub.aggregate_and_report(metric_name=rand_metric, value=rand_value)
            self.assertIn(rand_exception_msg, str(ctx.exception))

    def test_generate_final_report_delegates(self):
        expected_report = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "metrics": [random.randint(1, 50) for _ in range(3)]
        }

        with patch.object(self.audit_hub.aggregator, 'generate_final_report', return_value=expected_report) as mock_gen:
            res = self.audit_hub.generate_final_report()
            mock_gen.assert_called_once()
            self.assertEqual(res, expected_report)


if __name__ == '__main__':
    unittest.main()