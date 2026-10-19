import unittest
from unittest.mock import patch
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHubRefactored(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(1.0, 100.0)
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def test_init_sets_attributes(self):
        self.assertEqual(self.hub.aggregator.repo_path, self.repo_path)
        self.assertEqual(self.hub.aggregator.threshold, self.threshold)
        self.assertEqual(self.hub.logger.log_path, self.log_path)

    def test_log_anomaly_delegates_to_logger(self):
        source = f"source_{uuid.uuid4().hex}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_snapshot = {uuid.uuid4().hex: random.random()}

        expected_return = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.hub.logger, "log_anomaly", return_value=expected_return) as mock_log:
            res = self.hub.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )
            mock_log.assert_called_once_with(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )
            self.assertEqual(res, expected_return)

    def test_aggregate_and_report_handles_string_anomaly_gracefully(self):
        metric_name = f"metric_{uuid.uuid4().hex}"
        value = random.uniform(0.0, 1000.0)

        malformed_string_anomaly = uuid.uuid4().hex

        with patch.object(self.hub.aggregator, "aggregate_and_report") as mock_agg:
            mock_agg.return_value = malformed_string_anomaly

            res = self.hub.aggregate_and_report(metric_name=metric_name, value=value)

            mock_agg.assert_called_once_with(metric_name=metric_name, value=value)
            self.assertEqual(res, malformed_string_anomaly)

    def test_aggregate_and_report_standard_flow(self):
        metric_name = f"metric_{uuid.uuid4().hex}"
        value = random.uniform(0.0, 1000.0)
        expected_dict_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.hub.aggregator, "aggregate_and_report", return_value=expected_dict_result) as mock_agg:
            res = self.hub.aggregate_and_report(metric_name=metric_name, value=value)
            mock_agg.assert_called_once_with(metric_name=metric_name, value=value)
            self.assertEqual(res, expected_dict_result)

    def test_generate_final_report_delegates(self):
        expected_report = {uuid.uuid4().hex: "".join(random.choices(string.ascii_letters, k=10))}

        with patch.object(self.hub.aggregator, "generate_final_report", return_value=expected_report) as mock_gen:
            res = self.hub.generate_final_report()
            mock_gen.assert_called_once()
            self.assertEqual(res, expected_report)

if __name__ == "__main__":
    unittest.main()