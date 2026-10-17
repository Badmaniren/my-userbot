import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.anomaly_correlator import AnomalyCorrelator, AnomalyCorrelatorError
from skills.anomaly_detector import AnomalyDetectorError


class TestAnomalyCorrelator(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 99.9)

    def test_init_default_detectors_and_loggers(self):
        correlator = AnomalyCorrelator(repo_path=self.repo_path, log_path=self.log_path, threshold=self.threshold)
        self.assertIsNotNone(correlator.detector)
        self.assertIsNotNone(correlator.logger)

    def test_init_with_injected_mocks(self):
        mock_detector = MagicMock()
        mock_logger = MagicMock()
        correlator = AnomalyCorrelator(detector=mock_detector, logger=mock_logger)
        self.assertEqual(correlator.detector, mock_detector)
        self.assertEqual(correlator.logger, mock_logger)

    def test_correlate_metric_success_anomaly_detected(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = random.uniform(100.0, 500.0)

        mock_detector = MagicMock()
        mock_detector.detect_anomaly.return_value = True
        mock_logger = MagicMock()

        correlator = AnomalyCorrelator(detector=mock_detector, logger=mock_logger)
        res = correlator.correlate_metric(metric_name, metric_value)

        self.assertTrue(res)
        mock_detector.record_metric.assert_called_once_with(metric_name, metric_value)
        mock_detector.detect_anomaly.assert_called_once_with(metric_name, metric_value)
        mock_logger.log_anomaly.assert_called_once_with(metric_name)

    def test_correlate_metric_success_no_anomaly(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = random.uniform(0.0, 50.0)

        mock_detector = MagicMock()
        mock_detector.detect_anomaly.return_value = False
        mock_logger = MagicMock()

        correlator = AnomalyCorrelator(detector=mock_detector, logger=mock_logger)
        res = correlator.correlate_metric(metric_name, metric_value)

        self.assertFalse(res)
        mock_detector.record_metric.assert_called_once_with(metric_name, metric_value)
        mock_detector.detect_anomaly.assert_called_once_with(metric_name, metric_value)
        mock_logger.log_anomaly.assert_not_called()

    def test_correlate_metric_detector_error_raises_correlator_error(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = random.uniform(1.0, 10.0)
        error_msg = f"error_{uuid.uuid4().hex}"

        mock_detector = MagicMock()
        mock_detector.record_metric.side_effect = AnomalyDetectorError(error_msg)
        mock_logger = MagicMock()

        correlator = AnomalyCorrelator(detector=mock_detector, logger=mock_logger)
        with self.assertRaises(AnomalyCorrelatorError) as ctx:
            correlator.correlate_metric(metric_name, metric_value)
        self.assertIn(error_msg, str(ctx.exception))

    def test_analyze_execution_flow(self):
        exec_id = uuid.uuid4().hex
        payload_key = f"key_{uuid.uuid4().hex[:6]}"
        payload_val = random.randint(1, 1000)
        metrics_payload = {payload_key: payload_val}

        expected_analysis = {f"res_{uuid.uuid4().hex[:4]}": random.random()}

        mock_detector = MagicMock()
        mock_detector.analyze_execution_metrics.return_value = expected_analysis
        correlator = AnomalyCorrelator(detector=mock_detector)

        result = correlator.analyze_execution_flow(exec_id, metrics_payload)
        self.assertEqual(result, expected_analysis)
        mock_detector.analyze_execution_metrics.assert_called_once_with(exec_id, metrics_payload)

    def test_get_correlation_report(self):
        report_data = {uuid.uuid4().hex: uuid.uuid4().hex, "status": "stable"}

        mock_logger = MagicMock()
        mock_logger.get_structured_report.return_value = report_data
        correlator = AnomalyCorrelator(logger=mock_logger)

        report = correlator.get_correlation_report()
        self.assertEqual(report, report_data)
        mock_logger.get_structured_report.assert_called_once()

    def test_correlate_events(self):
        anomalies_list = [uuid.uuid4().hex, uuid.uuid4().hex]
        report_data = {uuid.uuid4().hex: random.randint(10, 50)}

        mock_logger = MagicMock()
        mock_logger.get_anomalies.return_value = anomalies_list
        mock_logger.get_structured_report.return_value = report_data
        correlator = AnomalyCorrelator(logger=mock_logger)

        res = correlator.correlate_events()
        self.assertIsInstance(res, dict)
        self.assertEqual(res["correlated_count"], len(anomalies_list))
        self.assertEqual(res["report"], report_data)
        mock_logger.get_anomalies.assert_called_once()
        mock_logger.get_structured_report.assert_called_once()


if __name__ == "__main__":
    unittest.main()