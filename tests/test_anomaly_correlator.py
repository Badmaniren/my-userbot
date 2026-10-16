import unittest
from unittest.mock import MagicMock, patch
import uuid
import random

from skills.anomaly_correlator import AnomalyCorrelator, AnomalyCorrelatorError
from skills.anomaly_detector import AnomalyDetectorError


class TestAnomalyCorrelatorInquisition(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 0.9)
        
        self.mock_detector = MagicMock()
        self.mock_logger = MagicMock()
        
        self.correlator = AnomalyCorrelator(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold,
            detector=self.mock_detector,
            logger=self.mock_logger
        )

    def test_init_creates_default_instances(self):
        with patch('skills.anomaly_correlator.AnomalyDetector') as det_patch, \
             patch('skills.anomaly_correlator.AnomalyLogger') as log_patch:
            
            r_path = f"/tmp/{uuid.uuid4().hex}"
            l_path = f"/tmp/{uuid.uuid4().hex}.log"
            thresh = random.uniform(0.5, 0.99)
            
            corr = AnomalyCorrelator(repo_path=r_path, log_path=l_path, threshold=thresh)
            
            det_patch.assert_called_once_with(
                repo_path=r_path,
                threshold=thresh,
                git_inspector=None,
                patch_verifier=None
            )
            log_patch.assert_called_once_with(log_path=l_path)
            self.assertIs(corr.detector, det_patch.return_value)
            self.assertIs(corr.logger, log_patch.return_value)

    def test_correlate_metric_anomaly_detected(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        value = random.uniform(10.0, 100.0)
        
        self.mock_detector.detect_anomaly.return_value = True

        result = self.correlator.correlate_metric(metric_name, value)

        self.assertTrue(result)
        self.mock_detector.record_metric.assert_called_once_with(metric_name, value)
        self.mock_detector.detect_anomaly.assert_called_once_with(metric_name, value)
        self.mock_logger.log_anomaly.assert_called_once_with(metric_name)

    def test_correlate_metric_no_anomaly(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        value = random.uniform(0.0, 5.0)
        
        self.mock_detector.detect_anomaly.return_value = False

        result = self.correlator.correlate_metric(metric_name, value)

        self.assertFalse(result)
        self.mock_detector.record_metric.assert_called_once_with(metric_name, value)
        self.mock_detector.detect_anomaly.assert_called_once_with(metric_name, value)
        self.mock_logger.log_anomaly.assert_not_called()

    def test_correlate_metric_raises_correlator_error_on_detector_failure(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        value = random.uniform(1.0, 10.0)
        error_msg = f"detector_failure_{uuid.uuid4().hex[:6]}"
        
        self.mock_detector.record_metric.side_effect = AnomalyDetectorError(error_msg)

        with self.assertRaises(AnomalyCorrelatorError) as ctx:
            self.correlator.correlate_metric(metric_name, value)

        self.assertIn(error_msg, str(ctx.exception))

    def test_analyze_execution_flow(self):
        execution_id = f"exec_{uuid.uuid4().hex[:8]}"
        metrics_payload = {f"key_{uuid.uuid4().hex[:4]}": random.randint(1, 100)}
        expected_analysis = {f"result_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex}
        
        self.mock_detector.analyze_execution_metrics.return_value = expected_analysis

        result = self.correlator.analyze_execution_flow(execution_id, metrics_payload)

        self.assertEqual(result, expected_analysis)
        self.mock_detector.analyze_execution_metrics.assert_called_once_with(execution_id, metrics_payload)

    def test_get_correlation_report(self):
        expected_report = {f"section_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex}
        self.mock_logger.get_structured_report.return_value = expected_report

        result = self.correlator.get_correlation_report()

        self.assertEqual(result, expected_report)
        self.mock_logger.get_structured_report.assert_called_once()

    def test_correlate_events(self):
        anomalies_list = [f"anomaly_{uuid.uuid4().hex[:4]}" for _ in range(random.randint(1, 5))]
        structured_report = {f"rep_{uuid.uuid4().hex[:4]}": random.random()}
        
        self.mock_logger.get_anomalies.return_value = anomalies_list
        self.mock_logger.get_structured_report.return_value = structured_report

        result = self.correlator.correlate_events()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["correlated_count"], len(anomalies_list))
        self.assertEqual(result["report"], structured_report)
        self.mock_logger.get_anomalies.assert_called_once()
        self.mock_logger.get_structured_report.assert_called_once()


if __name__ == '__main__':
    unittest.main()