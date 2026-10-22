import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub, AnomalyAuditHubError

class TestAnomalyAuditHub(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.log_path = f"/logs/{uuid.uuid4().hex}.log"
        self.threshold = round(random.uniform(0.1, 99.9), 2)

        with patch('skills.anomaly_audit_hub.AnomalyLogger') as mock_logger_cls, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as mock_aggregator_cls:

            self.mock_logger_instance = mock_logger_cls.return_value
            self.mock_aggregator_instance = mock_aggregator_cls.return_value

            self.hub = AnomalyAuditHub(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

    def test_init_instantiates_dependencies(self):
        with patch('skills.anomaly_audit_hub.AnomalyLogger') as mock_logger_cls, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as mock_aggregator_cls:

            r_path = f"/repo/{uuid.uuid4().hex}"
            l_path = f"/logs/{uuid.uuid4().hex}.log"
            thresh = round(random.uniform(1.0, 50.0), 2)

            AnomalyAuditHub(repo_path=r_path, log_path=l_path, threshold=thresh)

            mock_logger_cls.assert_called_once_with(log_path=l_path)
            mock_aggregator_cls.assert_called_once_with(
                repo_path=r_path,
                log_path=l_path,
                threshold=thresh,
                logger=mock_logger_cls.return_value
            )

    def test_log_anomaly_delegates_correctly(self):
        source = f"source_{uuid.uuid4().hex[:6]}"
        severity = random.choice(["INFO", "WARNING", "CRITICAL", "FATAL"])
        details = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_snapshot = {uuid.uuid4().hex: random.randint(1, 1000)}

        expected_return = uuid.uuid4().hex
        self.mock_logger_instance.log_anomaly.return_value = expected_return

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
        self.assertEqual(result, expected_return)

    def test_aggregate_and_report_delegates_correctly(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        value = round(random.uniform(-500.0, 500.0), 4)
        expected_return = {uuid.uuid4().hex: uuid.uuid4().hex}

        self.mock_aggregator_instance.aggregate_and_report.return_value = expected_return

        result = self.hub.aggregate_and_report(
            metric_name=metric_name,
            value=value
        )

        self.mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
            metric_name=metric_name,
            value=value
        )
        self.assertEqual(result, expected_return)

    def test_generate_final_report_delegates_correctly(self):
        expected_report = [uuid.uuid4().hex for _ in range(random.randint(1, 5))]
        self.mock_aggregator_instance.generate_final_report.return_value = expected_report

        result = self.hub.generate_final_report()

        self.mock_aggregator_instance.generate_final_report.assert_called_once()
        self.assertEqual(result, expected_report)

    def test_init_validation_raises_error(self):
        with self.assertRaises(AnomalyAuditHubError):
            AnomalyAuditHub(repo_path="", log_path="/path/log", threshold=0.5)
        with self.assertRaises(AnomalyAuditHubError):
            AnomalyAuditHub(repo_path="/repo", log_path="", threshold=0.5)
        with self.assertRaises(AnomalyAuditHubError):
            AnomalyAuditHub(repo_path="/repo", log_path="/path/log", threshold="invalid")

    def test_methods_raise_anomaly_audit_hub_error_on_failure(self):
        self.mock_logger_instance.log_anomaly.side_effect = RuntimeError("Log failed")
        with self.assertRaises(AnomalyAuditHubError):
            self.hub.log_anomaly("src", "HIGH", {}, {})

        self.mock_aggregator_instance.aggregate_and_report.side_effect = RuntimeError("Aggregate failed")
        with self.assertRaises(AnomalyAuditHubError):
            self.hub.aggregate_and_report("metric", 10.0)

        self.mock_aggregator_instance.generate_final_report.side_effect = RuntimeError("Report failed")
        with self.assertRaises(AnomalyAuditHubError):
            self.hub.generate_final_report()

if __name__ == '__main__':
    unittest.main()