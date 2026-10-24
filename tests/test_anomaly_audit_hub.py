import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHubIntegration(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.log_path = f"/tmp/log_{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 0.9)
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def test_init_sets_components(self):
        self.assertIsNotNone(self.audit_hub.logger)
        self.assertIsNotNone(self.audit_hub.aggregator)
        self.assertEqual(self.audit_hub.aggregator.threshold, self.threshold)
        self.assertEqual(self.audit_hub.aggregator.repo_path, self.repo_path)

    def test_log_anomaly_delegates_correctly(self):
        source_name = f"source_{uuid.uuid4().hex[:6]}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_dict = {uuid.uuid4().hex: random.randint(1, 100)}
        telemetry_dict = {uuid.uuid4().hex: random.random()}

        with patch.object(self.audit_hub.logger, 'log_anomaly') as mock_log:
            mock_log.return_value = uuid.uuid4().hex
            res = self.audit_hub.log_anomaly(
                source=source_name,
                severity=severity_level,
                details=details_dict,
                telemetry_snapshot=telemetry_dict
            )
            mock_log.assert_called_once_with(
                source=source_name,
                severity=severity_level,
                details=details_dict,
                telemetry_snapshot=telemetry_dict
            )
            self.assertEqual(res, mock_log.return_value)

    def test_aggregate_and_report_delegates_correctly(self):
        metric = f"metric_{uuid.uuid4().hex[:6]}"
        val = random.uniform(1.0, 100.0)
        expected_result = {uuid.uuid4().hex: random.randint(1, 50)}

        with patch.object(self.audit_hub.aggregator, 'aggregate_and_report') as mock_agg:
            mock_agg.return_value = expected_result
            res = self.audit_hub.aggregate_and_report(metric_name=metric, value=val)
            mock_agg.assert_called_once_with(metric_name=metric, value=val)
            self.assertEqual(res, expected_result)

    def test_generate_final_report_delegates_correctly(self):
        expected_report = {
            "report_id": uuid.uuid4().hex,
            "status": random.choice(["SECURE", "VULNERABLE", "WARNING"])
        }

        with patch.object(self.audit_hub.aggregator, 'generate_final_report') as mock_gen:
            mock_gen.return_value = expected_report
            res = self.audit_hub.generate_final_report()
            mock_gen.assert_called_once()
            self.assertEqual(res, expected_report)

    def test_end_to_end_audit_workflow(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        metric_value = random.uniform(10.0, 99.9)

        mock_aggregation_output = {
            "metric": metric_name,
            "value": metric_value,
            "flagged": True,
            "audit_uuid": uuid.uuid4().hex
        }

        mock_final_output = {
            "summary": "completed",
            "total_anomalies": random.randint(1, 10),
            "trace": uuid.uuid4().hex
        }

        with patch.object(self.audit_hub.aggregator, 'aggregate_and_report', return_value=mock_aggregation_output) as mock_agg_method, \
             patch.object(self.audit_hub.aggregator, 'generate_final_report', return_value=mock_final_output) as mock_gen_method:

            aggregation_result = self.audit_hub.aggregate_and_report(
                metric_name=metric_name,
                value=metric_value
            )

            self.assertEqual(aggregation_result["metric"], metric_name)
            self.assertEqual(aggregation_result["value"], metric_value)
            self.assertTrue(aggregation_result["flagged"])

            final_report = self.audit_hub.generate_final_report()

            self.assertEqual(final_report["summary"], "completed")
            self.assertEqual(final_report["trace"], mock_final_output["trace"])

            mock_agg_method.assert_called_once_with(metric_name=metric_name, value=metric_value)
            mock_gen_method.assert_called_once()

if __name__ == '__main__':
    unittest.main()