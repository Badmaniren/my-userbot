import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.anomaly_correlator import AnomalyCorrelator, AnomalyCorrelatorError
from skills.anomaly_detector import AnomalyDetectorError


class TestAnomalyCorrelator(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = round(random.uniform(0.1, 0.9), 2)
        
        self.mock_detector = MagicMock()
        self.mock_logger = MagicMock()

    def test_init_with_injected_dependencies(self):
        correlator = AnomalyCorrelator(
            detector=self.mock_detector,
            logger=self.mock_logger
        )
        self.assertEqual(correlator.detector, self.mock_detector)
        self.assertEqual(correlator.logger, self.mock_logger)

    @patch('skills.anomaly_correlator.AnomalyLogger')
    @patch('skills.anomaly_correlator.AnomalyDetector')
    def test_init_default_instantiation(self, mock_detector_cls, mock_logger_cls):
        instance_repo = f"/var/git/{uuid.uuid4().hex}"
        instance_log = f"/var/log/{uuid.uuid4().hex}"
        instance_threshold = round(random.uniform(1.0, 5.0), 2)

        correlator = AnomalyCorrelator(
            repo_path=instance_repo,
            log_path=instance_log,
            threshold=instance_threshold
        )

        mock_detector_cls.assert_called_once_with(
            repo_path=instance_repo,
            threshold=instance_threshold,
            git_inspector=None,
            patch_verifier=None
        )
        mock_logger_cls.assert_called_once_with(log_path=instance_log)

    def test_correlate_metric_anomaly_detected(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = random.randint(100, 1000)

        self.mock_detector.detect_anomaly.return_value = True

        correlator = AnomalyCorrelator(
            detector=self.mock_detector,
            logger=self.mock_logger
        )

        result = correlator.correlate_metric(metric_name, metric_value)

        self.assertTrue(result)
        self.mock_detector.record_metric.assert_called_once_with(metric_name, metric_value)
        self.mock_detector.detect_anomaly.assert_called_once_with(metric_name, metric_value)
        self.mock_logger.log_anomaly.assert_called_once_with(metric_name)

    def test_correlate_metric_no_anomaly(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = random.randint(1, 99)

        self.mock_detector.detect_anomaly.return_value = False

        correlator = AnomalyCorrelator(
            detector=self.mock_detector,
            logger=self.mock_logger
        )

        result = correlator.correlate_metric(metric_name, metric_value)

        self.assertFalse(result)
        self.mock_detector.record_metric.assert_called_once_with(metric_name, metric_value)
        self.mock_detector.detect_anomaly.assert_called_once_with(metric_name, metric_value)
        self.mock_logger.log_anomaly.assert_not_called()

    def test_correlate_metric_raises_correlator_error(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = random.randint(1000, 5000)
        error_msg = f"detector_failure_{uuid.uuid4().hex[:6]}"

        self.mock_detector.record_metric.side_effect = AnomalyDetectorError(error_msg)

        correlator = AnomalyCorrelator(
            detector=self.mock_detector,
            logger=self.mock_logger
        )

        with self.assertRaises(AnomalyCorrelatorError) as ctx:
            correlator.correlate_metric(metric_name, metric_value)

        self.assertIn(error_msg, str(ctx.exception))

    def test_analyze_execution_flow(self):
        execution_id = uuid.uuid4().hex
        metrics_payload = {
            f"key_{uuid.uuid4().hex[:4]}": random.random(),
            f"key_{uuid.uuid4().hex[:4]}": random.randint(0, 100)
        }
        expected_analysis = {f"result_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex}
        self.mock_detector.analyze_execution_metrics.return_value = expected_analysis

        correlator = AnomalyCorrelator(
            detector=self.mock_detector,
            logger=self.mock_logger
        )

        result = correlator.analyze_execution_flow(execution_id, metrics_payload)

        self.assertEqual(result, expected_analysis)
        self.mock_detector.analyze_execution_metrics.assert_called_once_with(execution_id, metrics_payload)

    def test_get_correlation_report(self):
        expected_report = {
            "report_id": uuid.uuid4().hex,
            "metrics_count": random.randint(5, 50)
        }
        self.mock_logger.get_structured_report.return_value = expected_report

        correlator = AnomalyCorrelator(
            detector=self.mock_detector,
            logger=self.mock_logger
        )

        result = correlator.get_correlation_report()

        self.assertEqual(result, expected_report)
        self.mock_logger.get_structured_report.assert_called_once()

    def test_correlate_events(self):
        anomaly_count = random.randint(1, 10)
        mock_anomalies = [uuid.uuid4().hex for _ in range(anomaly_count)]
        expected_report = {uuid.uuid4().hex: uuid.uuid4().hex}

        self.mock_logger.get_anomalies.return_value = mock_anomalies
        self.mock_logger.get_structured_report.return_value = expected_report

        correlator = AnomalyCorrelator(
            detector=self.mock_detector,
            logger=self.mock_logger
        )

        result = correlator.correlate_events()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["correlated_count"], anomaly_count)
        self.assertEqual(result["report"], expected_report)
        self.mock_logger.get_anomalies.assert_called_once()
        self.mock_logger.get_structured_report.assert_called_once()


if __name__ == '__main__':
    unittest.main()