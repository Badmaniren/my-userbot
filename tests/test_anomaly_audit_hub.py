import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_report_aggregator import AnomalyReportAggregatorError


class TestAnomalyAuditHub(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = round(random.uniform(0.1, 99.9), 2)

        with patch("skills.anomaly_audit_hub.AnomalyLogger"), \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator"):
            self.hub = AnomalyAuditHub(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

    def test_init_instantiates_dependencies(self):
        rand_repo = f"/var/repo_{uuid.uuid4().hex}"
        rand_log = f"/var/log_{uuid.uuid4().hex}.log"
        rand_thresh = round(random.uniform(1.0, 50.0), 2)

        with patch("skills.anomaly_audit_hub.AnomalyLogger") as mock_logger_cls, \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator") as mock_aggregator_cls:

            hub_instance = AnomalyAuditHub(
                repo_path=rand_repo,
                log_path=rand_log,
                threshold=rand_thresh
            )

            mock_logger_cls.assert_called_once_with(log_path=rand_log)
            mock_aggregator_cls.assert_called_once_with(
                repo_path=rand_repo,
                log_path=rand_log,
                threshold=rand_thresh,
                logger=hub_instance.logger
            )

    def test_log_anomaly_delegates_correctly(self):
        source_id = ''.join(random.choices(string.ascii_lowercase, k=10))
        severity_level = random.choice(["INFO", "WARNING", "CRITICAL", "FATAL"])
        details_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_snapshot = {uuid.uuid4().hex: random.random()}
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.hub.logger, 'log_anomaly', return_value=expected_result) as mock_log:
            result = self.hub.log_anomaly(
                source=source_id,
                severity=severity_level,
                details=details_data,
                telemetry_snapshot=telemetry_snapshot
            )

            mock_log.assert_called_once_with(
                source=source_id,
                severity=severity_level,
                details=details_data,
                telemetry_snapshot=telemetry_snapshot
            )
            self.assertEqual(result, expected_result)

    def test_aggregate_and_report_delegates_correctly(self):
        metric_key = f"metric_{uuid.uuid4().hex}"
        metric_val = round(random.uniform(-1000, 1000), 4)
        expected_aggregation = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch.object(self.hub.aggregator, 'aggregate_and_report', return_value=expected_aggregation) as mock_agg:
            result = self.hub.aggregate_and_report(
                metric_name=metric_key,
                value=metric_val
            )

            mock_agg.assert_called_once_with(
                metric_name=metric_key,
                value=metric_val
            )
            self.assertEqual(result, expected_aggregation)

    def test_generate_final_report_delegates_correctly(self):
        expected_report = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "status": random.choice(["STABLE", "UNSTABLE", "DEGRADED"])
        }

        with patch.object(self.hub.aggregator, 'generate_final_report', return_value=expected_report) as mock_gen:
            result = self.hub.generate_final_report()

            mock_gen.assert_called_once()
            self.assertEqual(result, expected_report)

    def test_aggregate_and_report_raises_custom_exception(self):
        metric_key = f"faulty_metric_{uuid.uuid4().hex}"
        metric_val = round(random.uniform(0, 10), 2)
        error_message = f"Aggregation failed for {uuid.uuid4().hex}"

        with patch.object(self.hub.aggregator, 'aggregate_and_report', side_effect=AnomalyReportAggregatorError(error_message)):
            with self.assertRaises(AnomalyReportAggregatorError) as ctx:
                self.hub.aggregate_and_report(metric_name=metric_key, value=metric_val)

            self.assertIn(error_message, str(ctx.exception))


if __name__ == '__main__':
    unittest.main()