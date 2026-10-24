import unittest
from unittest.mock import patch
import uuid
import random
import io
from skills.anomaly_audit_hub import AnomalyAuditHub

class TestAnomalyAuditHub(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 99.9)

        with patch("skills.anomaly_audit_hub.AnomalyLogger") as mock_logger_cls, \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator") as mock_aggregator_cls:

            self.mock_logger_instance = mock_logger_cls.return_value
            self.mock_aggregator_instance = mock_aggregator_cls.return_value

            self.hub = AnomalyAuditHub(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

    def test_init_initializes_dependencies(self):
        rnd_repo = f"/var/repo/{uuid.uuid4().hex}"
        rnd_log = f"/var/log/{uuid.uuid4().hex}.log"
        rnd_thresh = random.uniform(1.0, 50.0)

        with patch("skills.anomaly_audit_hub.AnomalyLogger") as mock_logger_cls, \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator") as mock_aggregator_cls:

            hub_instance = AnomalyAuditHub(
                repo_path=rnd_repo,
                log_path=rnd_log,
                threshold=rnd_thresh
            )

            mock_logger_cls.assert_called_once_with(log_path=rnd_log)
            mock_aggregator_cls.assert_called_once_with(
                repo_path=rnd_repo,
                log_path=rnd_log,
                threshold=rnd_thresh,
                logger=mock_logger_cls.return_value
            )
            self.assertEqual(hub_instance.logger, mock_logger_cls.return_value)
            self.assertEqual(hub_instance.aggregator, mock_aggregator_cls.return_value)

    def test_log_anomaly_delegates_correctly(self):
        rnd_source = f"source_{uuid.uuid4().hex}"
        rnd_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rnd_details = {uuid.uuid4().hex: uuid.uuid4().hex}
        rnd_snapshot = {uuid.uuid4().hex: random.randint(0, 1000)}
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        self.mock_logger_instance.log_anomaly.return_value = expected_result

        result = self.hub.log_anomaly(
            source=rnd_source,
            severity=rnd_severity,
            details=rnd_details,
            telemetry_snapshot=rnd_snapshot
        )

        self.mock_logger_instance.log_anomaly.assert_called_once_with(
            source=rnd_source,
            severity=rnd_severity,
            details=rnd_details,
            telemetry_snapshot=rnd_snapshot
        )
        self.assertEqual(result, expected_result)

    def test_aggregate_and_report_delegates_correctly(self):
        rnd_metric = f"metric_{uuid.uuid4().hex}"
        rnd_value = random.uniform(-100.0, 100.0)
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        self.mock_aggregator_instance.aggregate_and_report.return_value = expected_result

        result = self.hub.aggregate_and_report(
            metric_name=rnd_metric,
            value=rnd_value
        )

        self.mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
            metric_name=rnd_metric,
            value=rnd_value
        )
        self.assertEqual(result, expected_result)

    def test_generate_final_report_delegates_correctly(self):
        expected_result = f"report_{uuid.uuid4().hex}"
        self.mock_aggregator_instance.generate_final_report.return_value = expected_result

        result = self.hub.generate_final_report()

        self.mock_aggregator_instance.generate_final_report.assert_called_once()
        self.assertEqual(result, expected_result)

    def test_log_anomaly_with_stream_mock(self):
        rnd_source = uuid.uuid4().hex
        rnd_severity = uuid.uuid4().hex
        stream_data = io.BytesIO(f"data_{uuid.uuid4().hex}".encode('utf-8'))
        rnd_details = {"stream": stream_data}
        rnd_snapshot = {"uptime": random.randint(100, 9999)}

        expected_val = uuid.uuid4().hex
        self.mock_logger_instance.log_anomaly.return_value = expected_val

        res = self.hub.log_anomaly(rnd_source, rnd_severity, rnd_details, rnd_snapshot)

        self.assertEqual(res, expected_val)
        self.mock_logger_instance.log_anomaly.assert_called_once_with(
            source=rnd_source,
            severity=rnd_severity,
            details=rnd_details,
            telemetry_snapshot=rnd_snapshot
        )

if __name__ == "__main__":
    unittest.main()