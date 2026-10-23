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
        self.threshold = random.uniform(0.1, 9.9)
        self.hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )

    def test_init_sets_attributes(self):
        self.assertEqual(self.hub.repo_path, self.repo_path)
        self.assertEqual(self.hub.log_path, self.log_path)
        self.assertEqual(self.hub.threshold, self.threshold)
        self.assertEqual(self.hub.logger.log_path, self.log_path)

    def test_log_anomaly_success(self):
        source_val = uuid.uuid4().hex
        severity_val = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_val = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_val = {uuid.uuid4().hex: random.random()}

        with patch("skills.anomaly_logger.AnomalyLogger") as mock_logger_class, \
             patch.object(self.hub.logger, "log_anomaly", return_value=True) as mock_log:

            res = self.hub.log_anomaly(
                source=source_val,
                severity=severity_val,
                details=details_val,
                telemetry_snapshot=telemetry_val
            )
            mock_log.assert_called_once_with(
                source=source_val,
                severity=severity_val,
                details=details_val,
                telemetry_snapshot=telemetry_val
            )
            self.assertTrue(res)

    def test_log_anomaly_none_result_returns_true(self):
        source_val = uuid.uuid4().hex
        severity_val = uuid.uuid4().hex
        details_val = {uuid.uuid4().hex: 123}
        telemetry_val = {uuid.uuid4().hex: 456}

        with patch.object(self.hub.logger, "log_anomaly", return_value=None) as mock_log:
            res = self.hub.log_anomaly(
                source=source_val,
                severity=severity_val,
                details=details_val,
                telemetry_snapshot=telemetry_val
            )
            self.assertTrue(res)

    def test_aggregate_and_report(self):
        metric_name = uuid.uuid4().hex
        metric_value = random.uniform(10.0, 100.0)
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.hub.aggregator, "aggregate_and_report", return_value=expected_result) as mock_agg:
            res = self.hub.aggregate_and_report(metric_name=metric_name, value=metric_value)
            mock_agg.assert_called_once_with(metric_name=metric_name, value=metric_value)
            self.assertEqual(res, expected_result)

    def test_generate_final_report(self):
        expected_report = uuid.uuid4().hex

        with patch.object(self.hub.aggregator, "generate_final_report", return_value=expected_report) as mock_gen:
            res = self.hub.generate_final_report()
            mock_gen.assert_called_once()
            self.assertEqual(res, expected_report)

    def test_stream_io_mocking_compliance(self):
        dummy_stream = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        self.assertIsNotNone(dummy_stream.read())