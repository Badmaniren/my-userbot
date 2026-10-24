import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHub(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 1.0)

        with patch('skills.anomaly_audit_hub.AnomalyLogger') as MockLogger, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as MockAggregator:
            self.mock_logger = MockLogger.return_value
            self.mock_aggregator = MockAggregator.return_value
            self.hub = AnomalyAuditHub(self.repo_path, self.log_path, self.threshold)

    def test_log_anomaly_delegation(self):
        source = "".join(random.choices(string.ascii_letters, k=10))
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {"id": uuid.uuid4().hex, "val": random.random()}
        telemetry = {"cpu": random.randint(0, 100)}

        expected_result = {"status": "success", "id": uuid.uuid4().hex}
        self.mock_logger.log_anomaly.return_value = expected_result

        result = self.hub.log_anomaly(source, severity, details, telemetry)

        self.mock_logger.log_anomaly.assert_called_once_with(
            source=source,
            severity=severity,
            details=details,
            telemetry_snapshot=telemetry
        )
        self.assertEqual(result, expected_result)

    def test_aggregate_and_report_delegation(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        value = random.uniform(0, 1000)
        expected_report = {"processed": True, "metric": metric_name}

        self.mock_aggregator.aggregate_and_report.return_value = expected_report

        result = self.hub.aggregate_and_report(metric_name, value)

        self.mock_aggregator.aggregate_and_report.assert_called_once_with(
            metric_name=metric_name,
            value=value
        )
        self.assertEqual(result, expected_report)

    def test_generate_final_report_delegation(self):
        final_data = {
            "summary": "audit_complete",
            "uuid": uuid.uuid4().hex,
            "score": random.random()
        }
        self.mock_aggregator.generate_final_report.return_value = final_data

        result = self.hub.generate_final_report()

        self.mock_aggregator.generate_final_report.assert_called_once()
        self.assertEqual(result, final_data)

    def test_initialization_parameters(self):
        with patch('skills.anomaly_audit_hub.AnomalyLogger') as MockLogger, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as MockAggregator:

            repo = f"/repo/{uuid.uuid4().hex}"
            log = f"/log/{uuid.uuid4().hex}"
            thresh = random.random()

            hub = AnomalyAuditHub(repo, log, thresh)

            MockLogger.assert_called_with(log_path=log)
            MockAggregator.assert_called_with(
                repo_path=repo,
                log_path=log,
                threshold=thresh,
                logger=MockLogger.return_value
            )

if __name__ == '__main__':
    unittest.main()