import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHub(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/repo/{uuid.uuid4().hex}"
        self.rand_log = f"/logs/{uuid.uuid4().hex}.log"
        self.rand_threshold = round(random.uniform(0.1, 99.9), 2)

        with patch("skills.anomaly_audit_hub.AnomalyLogger") as mock_logger_cls, \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator") as mock_aggregator_cls:

            self.mock_logger_instance = mock_logger_cls.return_value
            self.mock_aggregator_instance = mock_aggregator_cls.return_value

            self.hub = AnomalyAuditHub(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.rand_threshold
            )

    def test_init_initializes_dependencies_correctly(self):
        with patch("skills.anomaly_audit_hub.AnomalyLogger") as mock_logger_cls, \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator") as mock_aggregator_cls:

            r_repo = uuid.uuid4().hex
            r_log = f"{uuid.uuid4().hex}.log"
            r_thresh = random.uniform(1.0, 10.0)

            AnomalyAuditHub(r_repo, r_log, r_thresh)

            mock_logger_cls.assert_called_once_with(log_path=r_log)
            mock_aggregator_cls.assert_called_once_with(
                repo_path=r_repo,
                log_path=r_log,
                threshold=r_thresh,
                logger=mock_logger_cls.return_value
            )

    def test_log_anomaly_delegates_to_logger(self):
        rand_source = ''.join(random.choices(string.ascii_letters, k=8))
        rand_severity = random.choice(["INFO", "WARNING", "CRITICAL", "FATAL"])
        rand_details = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_telemetry = {uuid.uuid4().hex: random.random()}
        expected_return = uuid.uuid4().hex

        self.mock_logger_instance.log_anomaly.return_value = expected_return

        result = self.hub.log_anomaly(
            source=rand_source,
            severity=rand_severity,
            details=rand_details,
            telemetry_snapshot=rand_telemetry
        )

        self.mock_logger_instance.log_anomaly.assert_called_once_with(
            source=rand_source,
            severity=rand_severity,
            details=rand_details,
            telemetry_snapshot=rand_telemetry
        )
        self.assertEqual(result, expected_return)

    def test_aggregate_and_report_delegates_to_aggregator(self):
        rand_metric = ''.join(random.choices(string.ascii_lowercase, k=10))
        rand_value = round(random.uniform(-1000, 1000), 4)
        expected_output = {uuid.uuid4().hex: uuid.uuid4().hex}

        self.mock_aggregator_instance.aggregate_and_report.return_value = expected_output

        result = self.hub.aggregate_and_report(
            metric_name=rand_metric,
            value=rand_value
        )

        self.mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
            metric_name=rand_metric,
            value=rand_value
        )
        self.assertEqual(result, expected_output)

    def test_generate_final_report_delegates_to_aggregator(self):
        expected_report = uuid.uuid4().hex
        self.mock_aggregator_instance.generate_final_report.return_value = expected_report

        result = self.hub.generate_final_report()

        self.mock_aggregator_instance.generate_final_report.assert_called_once()
        self.assertEqual(result, expected_report)

    def test_log_anomaly_exception_propagation(self):
        rand_source = uuid.uuid4().hex
        rand_severity = uuid.uuid4().hex
        self.mock_logger_instance.log_anomaly.side_effect = RuntimeError(uuid.uuid4().hex)

        with self.assertRaises(RuntimeError):
            self.hub.log_anomaly(rand_source, rand_severity, {}, {})

    def test_aggregate_and_report_exception_propagation(self):
        rand_metric = uuid.uuid4().hex
        rand_value = random.random()
        self.mock_aggregator_instance.aggregate_and_report.side_effect = ValueError(uuid.uuid4().hex)

        with self.assertRaises(ValueError):
            self.hub.aggregate_and_report(rand_metric, rand_value)

    def test_generate_final_report_exception_propagation(self):
        self.mock_aggregator_instance.generate_final_report.side_effect = TypeError(uuid.uuid4().hex)

        with self.assertRaises(TypeError):
            self.hub.generate_final_report()

    def test_validation_invalid_types(self):
        with self.assertRaises(TypeError):
            self.hub.log_anomaly("source", "HIGH", "invalid_details_str", {})

        with self.assertRaises(TypeError):
            self.hub.aggregate_and_report(12345, 50.0)

        with self.assertRaises(TypeError):
            self.hub.aggregate_and_report("metric", "invalid_value_str")

if __name__ == '__main__':
    unittest.main()