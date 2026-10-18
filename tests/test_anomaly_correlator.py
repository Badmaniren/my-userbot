import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.anomaly_correlator import AnomalyCorrelator, AnomalyCorrelatorError
from skills.anomaly_detector import AnomalyDetectorError


class TestAnomalyCorrelator(unittest.TestCase):

    def setUp(self):
        self.repo_path_val = uuid.uuid4().hex
        self.log_path_val = uuid.uuid4().hex
        self.threshold_val = random.uniform(0.1, 99.9)

    def test_init_with_defaults(self):
        with patch('skills.anomaly_correlator.AnomalyDetector') as mock_detector_cls, \
             patch('skills.anomaly_correlator.AnomalyLogger') as mock_logger_cls:
            
            correlator = AnomalyCorrelator(
                repo_path=self.repo_path_val,
                log_path=self.log_path_val,
                threshold=self.threshold_val
            )
            
            mock_detector_cls.assert_called_once_with(
                repo_path=self.repo_path_val,
                threshold=self.threshold_val,
                git_inspector=None,
                patch_verifier=None
            )
            mock_logger_cls.assert_called_once_with(log_path=self.log_path_val)

    def test_init_with_injected_dependencies(self):
        mock_detector = MagicMock()
        mock_logger = MagicMock()

        correlator = AnomalyCorrelator(detector=mock_detector, logger=mock_logger)

        self.assertEqual(correlator.detector, mock_detector)
        self.assertEqual(correlator.logger, mock_logger)

    def test_correlate_metric_anomaly_detected(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        metric_value = random.randint(1, 1000)

        mock_detector = MagicMock()
        mock_detector.detect_anomaly.return_value = True
        mock_logger = MagicMock()

        correlator = AnomalyCorrelator(detector=mock_detector, logger=mock_logger)
        result = correlator.correlate_metric(metric_name, metric_value)

        mock_detector.record_metric.assert_called_once_with(metric_name, metric_value)
        mock_detector.detect_anomaly.assert_called_once_with(metric_name, metric_value)
        mock_logger.log_anomaly.assert_called_once_with(metric_name)
        self.assertTrue(result)

    def test_correlate_metric_no_anomaly(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        metric_value = random.randint(1, 1000)

        mock_detector = MagicMock()
        mock_detector.detect_anomaly.return_value = False
        mock_logger = MagicMock()

        correlator = AnomalyCorrelator(detector=mock_detector, logger=mock_logger)
        result = correlator.correlate_metric(metric_name, metric_value)

        mock_detector.record_metric.assert_called_once_with(metric_name, metric_value)
        mock_detector.detect_anomaly.assert_called_once_with(metric_name, metric_value)
        mock_logger.log_anomaly.assert_not_called()
        self.assertFalse(result)

    def test_correlate_metric_detector_error(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        metric_value = random.randint(1, 1000)
        error_message = uuid.uuid4().hex

        mock_detector = MagicMock()
        mock_detector.record_metric.side_effect = AnomalyDetectorError(error_message)
        mock_logger = MagicMock()

        correlator = AnomalyCorrelator(detector=mock_detector, logger=mock_logger)

        with self.assertRaises(AnomalyCorrelatorError) as ctx:
            correlator.correlate_metric(metric_name, metric_value)

        self.assertIn(error_message, str(ctx.exception))

    def test_analyze_execution_flow(self):
        execution_id = uuid.uuid4().hex
        metrics_payload = {uuid.uuid4().hex: random.random() for _ in range(3)}
        expected_analysis = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_detector = MagicMock()
        mock_detector.analyze_execution_metrics.return_value = expected_analysis
        mock_logger = MagicMock()

        correlator = AnomalyCorrelator(detector=mock_detector, logger=mock_logger)
        result = correlator.analyze_execution_flow(execution_id, metrics_payload)

        mock_detector.analyze_execution_metrics.assert_called_once_with(execution_id, metrics_payload)
        self.assertEqual(result, expected_analysis)

    def test_get_correlation_report(self):
        expected_report = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_detector = MagicMock()
        mock_logger = MagicMock()
        mock_logger.get_structured_report.return_value = expected_report

        correlator = AnomalyCorrelator(detector=mock_detector, logger=mock_logger)
        result = correlator.get_correlation_report()

        mock_logger.get_structured_report.assert_called_once()
        self.assertEqual(result, expected_report)

    def test_correlate_events(self):
        anomalies_list = [uuid.uuid4().hex, uuid.uuid4().hex]
        structured_report = {uuid.uuid4().hex: random.randint(10, 50)}

        mock_detector = MagicMock()
        mock_logger = MagicMock()
        mock_logger.get_anomalies.return_value = anomalies_list
        mock_logger.get_structured_report.return_value = structured_report

        correlator = AnomalyCorrelator(detector=mock_detector, logger=mock_logger)
        result = correlator.correlate_events()

        mock_logger.get_anomalies.assert_called_once()
        mock_logger.get_structured_report.assert_called_once()
        
        self.assertEqual(result, {
            "correlated_count": len(anomalies_list),
            "report": structured_report
        })


if __name__ == '__main__':
    unittest.main()