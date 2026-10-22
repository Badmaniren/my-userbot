import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_report_aggregator import AnomalyReportAggregatorError


class TestAnomalyAuditHubInquisition(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = round(random.uniform(0.1, 0.9), 2)

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def test_init_and_public_signatures(self):
        rnd_source = "".join(random.choices(string.ascii_lowercase, k=10))
        rnd_severity = random.choice(["INFO", "WARNING", "CRITICAL", "FATAL"])
        rnd_details = {uuid.uuid4().hex: uuid.uuid4().hex}
        rnd_telemetry = {uuid.uuid4().hex: random.randint(1, 100)}

        with patch.object(self.audit_hub.logger, "log_anomaly", return_value=True) as mock_log:
            res = self.audit_hub.log_anomaly(
                source=rnd_source,
                severity=rnd_severity,
                details=rnd_details,
                telemetry_snapshot=rnd_telemetry
            )
            self.assertTrue(res)
            mock_log.assert_called_once_with(
                source=rnd_source,
                severity=rnd_severity,
                details=rnd_details,
                telemetry_snapshot=rnd_telemetry
            )

    def test_aggregate_and_report_success(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(10.0, 500.0), 2)
        expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.audit_hub.aggregator, "aggregate_and_report", return_value=expected_output) as mock_agg:
            result = self.audit_hub.aggregate_and_report(metric_name=metric_name, value=metric_value)
            self.assertEqual(result, expected_output)
            mock_agg.assert_called_once_with(metric_name=metric_name, value=metric_value)

    def test_aggregate_and_report_custom_exception(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(1.0, 10.0), 2)
        rnd_error_msg = f"Error_{uuid.uuid4().hex}"

        with patch.object(self.audit_hub.aggregator, "aggregate_and_report", side_effect=AnomalyReportAggregatorError(rnd_error_msg)):
            with self.assertRaises(AnomalyReportAggregatorError) as ctx:
                self.audit_hub.aggregate_and_report(metric_name=metric_name, value=metric_value)
            self.assertIn(rnd_error_msg, str(ctx.exception))

    def test_aggregate_and_report_wraps_unexpected_exception(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = round(random.uniform(1.0, 10.0), 2)
        rnd_error_msg = f"Unexpected_{uuid.uuid4().hex}"

        with patch.object(self.audit_hub.aggregator, "aggregate_and_report", side_effect=ValueError(rnd_error_msg)):
            with self.assertRaises(AnomalyReportAggregatorError) as ctx:
                self.audit_hub.aggregate_and_report(metric_name=metric_name, value=metric_value)
            self.assertIn(rnd_error_msg, str(ctx.exception))

    def test_generate_final_report_success(self):
        expected_report = {uuid.uuid4().hex: random.randint(100, 999)}

        with patch.object(self.audit_hub.aggregator, "generate_final_report", return_value=expected_report) as mock_gen:
            res = self.audit_hub.generate_final_report()
            self.assertEqual(res, expected_report)
            mock_gen.assert_called_once()

    def test_generate_final_report_custom_exception(self):
        rnd_error_msg = f"CriticalReportError_{uuid.uuid4().hex}"

        with patch.object(self.audit_hub.aggregator, "generate_final_report", side_effect=AnomalyReportAggregatorError(rnd_error_msg)):
            with self.assertRaises(AnomalyReportAggregatorError) as ctx:
                self.audit_hub.generate_final_report()
            self.assertIn(rnd_error_msg, str(ctx.exception))

    def test_generate_final_report_wraps_unexpected_exception(self):
        rnd_error_msg = f"RuntimeFail_{uuid.uuid4().hex}"

        with patch.object(self.audit_hub.aggregator, "generate_final_report", side_effect=RuntimeError(rnd_error_msg)):
            with self.assertRaises(AnomalyReportAggregatorError) as ctx:
                self.audit_hub.generate_final_report()
            self.assertIn(rnd_error_msg, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()