import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_report_aggregator import AnomalyReportAggregator


class TestAnomalyAuditHub(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 99.9)

        with patch('skills.anomaly_audit_hub.AnomalyLogger') as mock_logger_cls, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as mock_agg_cls:

            self.mock_logger_instance = mock_logger_cls.return_value
            self.mock_aggregator_instance = mock_agg_cls.return_value

            self.hub = AnomalyAuditHub(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold
            )

    def test_init_initialization_parameters(self):
        with patch('skills.anomaly_audit_hub.AnomalyLogger') as mock_logger_cls, \
             patch('skills.anomaly_audit_hub.AnomalyReportAggregator') as mock_agg_cls:

            r_path = f"/repo/{uuid.uuid4().hex}"
            l_path = f"/logs/{uuid.uuid4().hex}.log"
            thresh = random.uniform(1.0, 10.0)

            hub = AnomalyAuditHub(repo_path=r_path, log_path=l_path, threshold=thresh)

            mock_logger_cls.assert_called_once_with(log_path=l_path)
            mock_agg_cls.assert_called_once_with(
                repo_path=r_path,
                log_path=l_path,
                threshold=thresh,
                logger=hub.logger
            )

    def test_log_anomaly_success(self):
        source = uuid.uuid4().hex
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_snapshot = {uuid.uuid4().hex: random.randint(0, 1000)}

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

    def test_log_anomaly_propagates_exception(self):
        source = uuid.uuid4().hex
        severity = uuid.uuid4().hex
        details = {uuid.uuid4().hex: uuid.uuid4().hex}
        telemetry_snapshot = {uuid.uuid4().hex: random.random()}

        error_message = uuid.uuid4().hex
        self.mock_logger_instance.log_anomaly.side_effect = RuntimeError(error_message)

        with self.assertRaises(RuntimeError) as ctx:
            self.hub.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry_snapshot
            )

        self.assertIn(error_message, str(ctx.exception))

    def test_aggregate_and_report_success(self):
        metric_name = uuid.uuid4().hex
        value = random.uniform(-500.0, 500.0)
        expected_report = {uuid.uuid4().hex: uuid.uuid4().hex}

        self.mock_aggregator_instance.aggregate_and_report.return_value = expected_report

        result = self.hub.aggregate_and_report(metric_name=metric_name, value=value)

        self.mock_aggregator_instance.aggregate_and_report.assert_called_once_with(
            metric_name=metric_name,
            value=value
        )
        self.assertEqual(result, expected_report)

    def test_aggregate_and_report_propagates_exception(self):
        metric_name = uuid.uuid4().hex
        value = random.uniform(0.0, 100.0)
        error_message = uuid.uuid4().hex

        self.mock_aggregator_instance.aggregate_and_report.side_effect = ValueError(error_message)

        with self.assertRaises(ValueError) as ctx:
            self.hub.aggregate_and_report(metric_name=metric_name, value=value)

        self.assertIn(error_message, str(ctx.exception))

    def test_generate_final_report_success(self):
        expected_final_report = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            uuid.uuid4().hex: random.randint(1, 100)
        }
        self.mock_aggregator_instance.generate_final_report.return_value = expected_final_report

        result = self.hub.generate_final_report()

        self.mock_aggregator_instance.generate_final_report.assert_called_once()
        self.assertEqual(result, expected_final_report)

    def test_generate_final_report_propagates_exception(self):
        error_message = uuid.uuid4().hex
        self.mock_aggregator_instance.generate_final_report.side_effect = Exception(error_message)

        with self.assertRaises(Exception) as ctx:
            self.hub.generate_final_report()

        self.assertIn(error_message, str(ctx.exception))

    def test_integration_flow_with_real_components_mocked_io(self):
        real_log_path = f"/tmp/{uuid.uuid4().hex}.log"
        real_repo_path = f"/tmp/{uuid.uuid4().hex}"
        real_threshold = random.uniform(10.0, 50.0)

        mock_file_data = io.BytesIO(f"{uuid.uuid4().hex}\n".encode('utf-8'))

        with patch('builtins.open', return_value=mock_file_data) as mock_open, \
             patch('os.path.exists', return_value=True):

            hub = AnomalyAuditHub(
                repo_path=real_repo_path,
                log_path=real_log_path,
                threshold=real_threshold
            )

            self.assertIsInstance(hub.logger, AnomalyLogger)
            self.assertIsInstance(hub.aggregator, AnomalyReportAggregator)


if __name__ == '__main__':
    unittest.main()