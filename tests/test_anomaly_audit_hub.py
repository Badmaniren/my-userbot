import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
from skills.anomaly_audit_hub import AnomalyAuditHub

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

            r_path = f"/path/{uuid.uuid4().hex}"
            l_path = f"/path/{uuid.uuid4().hex}.log"
            thresh = random.random()

            hub = AnomalyAuditHub(repo_path=r_path, log_path=l_path, threshold=thresh)

            mock_logger_cls.assert_called_once_with(log_path=l_path)
            mock_aggregator_cls.assert_called_once_with(
                repo_path=r_path,
                log_path=l_path,
                threshold=thresh,
                logger=hub.logger
            )

    def test_log_anomaly_delegates_to_logger(self):
        source = f"source_{uuid.uuid4().hex[:6]}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_snapshot = {uuid.uuid4().hex: random.randint(1, 1000)}

        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}
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
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        value = round(random.uniform(-500.0, 500.0), 4)
        expected_aggregate = {uuid.uuid4().hex: random.random()}

        self.mock_aggregator_instance.aggregate_and_report.return_value = expected_aggregate

        result = self.hub.aggregate_and_report(metric_name=metric_name, value=value)

        self.mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
            metric_name=metric_name,
            value=value
        )
        self.assertEqual(result, expected_aggregate)

    def test_generate_final_report_delegates_to_aggregator(self):
        expected_report = f"report_content_{uuid.uuid4().hex}"
        self.mock_aggregator_instance.generate_final_report.return_value = expected_report

        result = self.hub.generate_final_report()

        self.mock_aggregator_instance.generate_final_report.assert_called_once()
        self.assertEqual(result, expected_report)

if __name__ == '__main__':
    unittest.main()