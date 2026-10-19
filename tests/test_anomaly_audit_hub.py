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

        with patch('skills.anomaly_audit_hub.AnomalyLogger') as mock_logger_cls, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as mock_agg_cls:

            self.mock_logger_instance = mock_logger_cls.return_value
            self.mock_agg_instance = mock_agg_cls.return_value

            self.hub = AnomalyAuditHub(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

    def test_init_initializes_dependencies_correctly(self):
        rand_repo = f"/repo/{uuid.uuid4().hex}"
        rand_log = f"/log/{uuid.uuid4().hex}.log"
        rand_thresh = random.uniform(1.0, 50.0)

        with patch('skills.anomaly_audit_hub.AnomalyLogger') as mock_logger_cls, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as mock_agg_cls:

            AnomalyAuditHub(repo_path=rand_repo, log_path=rand_log, threshold=rand_thresh)

            mock_logger_cls.assert_called_once_with(log_path=rand_log)
            mock_agg_cls.assert_called_once_with(
                repo_path=rand_repo,
                log_path=rand_log,
                threshold=rand_thresh,
                logger=mock_logger_cls.return_value
            )

    def test_log_anomaly_delegates_to_logger(self):
        source = "".join(random.choices(string.ascii_letters, k=10))
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_snapshot = {uuid.uuid4().hex: random.random()}
        expected_result = uuid.uuid4().hex

        self.mock_logger_instance.log_anomaly.return_value = expected_result

        result = self.hub.log_anomaly(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )

        self.mock_logger_instance.log_anomaly.assert_called_once_with(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry_snapshot
        )
        self.assertEqual(result, expected_result)

    def test_aggregate_and_report_delegates_to_aggregator(self):
        metric_name = "".join(random.choices(string.ascii_lowercase, k=8))
        value = random.uniform(-1000.0, 1000.0)
        expected_result = {uuid.uuid4().hex: random.randint(1, 100)}

        self.mock_agg_instance.aggregate_and_report.return_value = expected_result

        result = self.hub.aggregate_and_report(metric_name=metric_name, value=value)

        self.mock_agg_instance.aggregate_and_report.assert_called_once_with(
            metric_name=metric_name,
            value=value
        )
        self.assertEqual(result, expected_result)

    def test_generate_final_report_delegates_to_aggregator(self):
        expected_report = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "status": random.choice(["OK", "FAIL", "WARNING"])
        }

        self.mock_agg_instance.generate_final_report.return_value = expected_report

        result = self.hub.generate_final_report()

        self.mock_agg_instance.generate_final_report.assert_called_once()
        self.assertEqual(result, expected_report)


if __name__ == '__main__':
    unittest.main()