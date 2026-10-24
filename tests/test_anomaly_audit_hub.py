import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHub(unittest.TestCase):

    def setUp(self):
        self.rand_repo_path = f"/repo/{uuid.uuid4().hex}"
        self.rand_log_path = f"/logs/{uuid.uuid4().hex}.log"
        self.rand_threshold = round(random.uniform(0.1, 99.9), 2)

        with patch('skills.anomaly_audit_hub.AnomalyLogger') as mock_logger_cls, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as mock_aggregator_cls:

            self.mock_logger_instance = mock_logger_cls.return_value
            self.mock_aggregator_instance = mock_aggregator_cls.return_value

            self.hub = AnomalyAuditHub(
                repo_path=self.rand_repo_path,
                log_path=self.rand_log_path,
                threshold=self.rand_threshold
            )

    def test_init_instantiates_dependencies(self):
        with patch('skills.anomaly_audit_hub.AnomalyLogger') as mock_logger_cls, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as mock_aggregator_cls:

            repo = f"/var/repo/{uuid.uuid4().hex}"
            log = f"/var/log/{uuid.uuid4().hex}"
            thresh = random.uniform(1.0, 10.0)

            hub_instance = AnomalyAuditHub(repo_path=repo, log_path=log, threshold=thresh)

            mock_logger_cls.assert_called_once_with(log_path=log)
            mock_aggregator_cls.assert_called_once_with(
                repo_path=repo,
                log_path=log,
                threshold=thresh,
                logger=hub_instance.logger
            )

    def test_log_anomaly_delegates_to_logger(self):
        rand_source = ''.join(random.choices(string.ascii_letters, k=10))
        rand_severity = random.choice(["INFO", "WARNING", "CRITICAL", "FATAL"])
        rand_details = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_snapshot = {uuid.uuid4().hex: random.randint(0, 1000)}

        expected_return = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_logger_instance.log_anomaly.return_value = expected_return

        result = self.hub.log_anomaly(
            source=rand_source,
            severity=rand_severity,
            details=rand_details,
            telemetry_snapshot=rand_snapshot
        )

        self.mock_logger_instance.log_anomaly.assert_called_once_with(
            source=rand_source,
            severity=rand_severity,
            details=rand_details,
            telemetry_snapshot=rand_snapshot
        )
        self.assertEqual(result, expected_return)

    def test_aggregate_and_report_delegates_to_aggregator(self):
        rand_metric = f"metric_{uuid.uuid4().hex[:6]}"
        rand_value = round(random.uniform(-500.0, 500.0), 4)
        expected_aggregation = {uuid.uuid4().hex: random.random()}

        self.mock_aggregator_instance.aggregate_and_report.return_value = expected_aggregation

        result = self.hub.aggregate_and_report(metric_name=rand_metric, value=rand_value)

        self.mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
            metric_name=rand_metric,
            value=rand_value
        )
        self.assertEqual(result, expected_aggregation)

    def test_generate_final_report_delegates_to_aggregator(self):
        expected_report = f"REPORT_{uuid.uuid4().hex}"
        self.mock_aggregator_instance.generate_final_report.return_value = expected_report

        result = self.hub.generate_final_report()

        self.mock_aggregator_instance.generate_final_report.assert_called_once()
        self.assertEqual(result, expected_report)


if __name__ == '__main__':
    unittest.main()