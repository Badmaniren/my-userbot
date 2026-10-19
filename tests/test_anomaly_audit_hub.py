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

    def test_init_and_delegation(self):
        source_val = ''.join(random.choices(string.ascii_lowercase, k=10))
        severity_val = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_val = {uuid.uuid4().hex: random.randint(1, 100)}
        telemetry_val = {uuid.uuid4().hex: random.random()}

        metric_name_val = ''.join(random.choices(string.ascii_lowercase, k=8))
        metric_value = random.uniform(1.0, 1000.0)

        expected_log_res = uuid.uuid4().hex
        expected_agg_res = uuid.uuid4().hex
        expected_gen_res = uuid.uuid4().hex

        with patch('skills.anomaly_audit_hub.AnomalyLogger') as MockLoggerClass, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as MockAggregatorClass:

            mock_logger_instance = MockLoggerClass.return_value
            mock_logger_instance.log_anomaly.return_value = expected_log_res

            mock_aggregator_instance = MockAggregatorClass.return_value
            mock_aggregator_instance.aggregate_and_report.return_value = expected_agg_res
            mock_aggregator_instance.generate_final_report.return_value = expected_gen_res

            hub = AnomalyAuditHub(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

            MockLoggerClass.assert_called_once_with(log_path=self.log_path)
            MockAggregatorClass.assert_called_once_with(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold,
                logger=mock_logger_instance
            )

            res_log = hub.log_anomaly(
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
            self.assertEqual(res_log, expected_log_res)

            res_agg = hub.aggregate_and_report(
                metric_name=metric_name_val,
                value=metric_value
            )
            mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
                metric_name=metric_name_val,
                value=metric_value
            )
            self.assertEqual(res_agg, expected_agg_res)

            res_gen = hub.generate_final_report()
            mock_aggregator_instance.generate_final_report.assert_called_once()
            self.assertEqual(res_gen, expected_gen_res)

    def test_log_anomaly_resilience_and_exceptions(self):
        source_val = uuid.uuid4().hex
        severity_val = uuid.uuid4().hex
        details_val = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_val = {uuid.uuid4().hex: random.randint(0, 500)}

        with patch('skills.anomaly_audit_hub.AnomalyLogger') as MockLoggerClass, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator'):

            mock_logger_instance = MockLoggerClass.return_value
            test_exception = RuntimeError(uuid.uuid4().hex)
            mock_logger_instance.log_anomaly.side_effect = test_exception

            hub = AnomalyAuditHub(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

            with self.assertRaises(RuntimeError) as ctx:
                hub.log_anomaly(
                    source=source_val,
                    severity=severity_val,
                    details=details_val,
                    telemetry_snapshot=telemetry_val
                )
            self.assertEqual(str(ctx.exception), str(test_exception))

    def test_aggregate_and_report_edge_cases(self):
        metric_name_val = uuid.uuid4().hex
        metric_value = random.uniform(-500.0, 500.0)

        with patch('skills.anomaly_audit_hub.AnomalyLogger'), \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as MockAggregatorClass:

            mock_aggregator_instance = MockAggregatorClass.return_value
            mock_aggregator_instance.aggregate_and_report.return_value = {uuid.uuid4().hex: metric_value}

            hub = AnomalyAuditHub(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

            result = hub.aggregate_and_report(metric_name=metric_name_val, value=metric_value)
            self.assertIsInstance(result, dict)
            self.assertIn(list(result.keys())[0], result)
            self.assertEqual(result[list(result.keys())[0]], metric_value)


if __name__ == '__main__':
    unittest.main()