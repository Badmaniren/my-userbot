import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditHub(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/{uuid.uuid4().hex}"
        self.rand_log = f"/tmp/{uuid.uuid4().hex}.log"
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

    def test_init_initializes_dependencies(self):
        with patch("skills.anomaly_audit_hub.AnomalyLogger") as mock_logger_cls, \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator") as mock_aggregator_cls:

            repo = f"/var/log/{uuid.uuid4().hex}"
            log = f"/var/tmp/{uuid.uuid4().hex}"
            thresh = random.uniform(1.0, 10.0)

            hub = AnomalyAuditHub(repo_path=repo, log_path=log, threshold=thresh)

            mock_logger_cls.assert_called_once_with(log_path=log)
            mock_aggregator_cls.assert_called_once_with(
                repo_path=repo,
                log_path=log,
                threshold=thresh,
                logger=hub.logger
            )

    def test_log_anomaly_delegates_correctly(self):
        source = "".join(random.choices(string.ascii_lowercase, k=10))
        severity = random.choice(["INFO", "WARNING", "CRITICAL", "ERROR"])
        details = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}
        telemetry_snapshot = {uuid.uuid4().hex: random.randint(0, 1000) for _ in range(2)}

        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_logger_instance.log_anomaly.return_value = expected_result

        res = self.hub.log_anomaly(
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
        self.assertEqual(res, expected_result)

    def test_aggregate_and_report_delegates_correctly(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        value = round(random.uniform(-500.0, 500.0), 4)

        expected_report = {uuid.uuid4().hex: random.random()}
        self.mock_aggregator_instance.aggregate_and_report.return_value = expected_report

        res = self.hub.aggregate_and_report(metric_name=metric_name, value=value)

        self.mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
            metric_name=metric_name,
            value=value
        )
        self.assertEqual(res, expected_report)

    def test_generate_final_report_delegates_correctly(self):
        expected_final = {uuid.uuid4().hex: [uuid.uuid4().hex, uuid.uuid4().hex]}
        self.mock_aggregator_instance.generate_final_report.return_value = expected_final

        res = self.hub.generate_final_report()

        self.mock_aggregator_instance.generate_final_report.assert_called_once()
        self.assertEqual(res, expected_final)

    def test_log_anomaly_exception_propagation(self):
        source = uuid.uuid4().hex
        severity = "FATAL"
        details = {}
        telemetry_snapshot = {}

        err_msg = f"Error_{uuid.uuid4().hex}"
        self.mock_logger_instance.log_anomaly.side_effect = RuntimeError(err_msg)

        with self.assertRaises(RuntimeError) as ctx:
            self.hub.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )

        self.assertIn(err_msg, str(ctx.exception))

    def test_aggregate_and_report_exception_propagation(self):
        metric_name = uuid.uuid4().hex
        value = random.random()

        err_msg = f"AggError_{uuid.uuid4().hex}"
        self.mock_aggregator_instance.aggregate_and_report.side_effect = ValueError(err_msg)

        with self.assertRaises(ValueError) as ctx:
            self.hub.aggregate_and_report(metric_name=metric_name, value=value)

        self.assertIn(err_msg, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()