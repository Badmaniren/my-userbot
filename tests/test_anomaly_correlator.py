import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.anomaly_correlator import AnomalyCorrelator, AnomalyCorrelatorError
from skills.anomaly_detector import AnomalyDetector, AnomalyDetectorError
from skills.anomaly_logger import AnomalyLogger


class TestAnomalyCorrelator(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/repo/{uuid.uuid4().hex}"
        self.rand_log = f"/logs/{uuid.uuid4().hex}.log"
        self.rand_metric = f"metric_{uuid.uuid4().hex[:8]}"
        self.rand_val = random.uniform(10.0, 1000.0)
        self.rand_target = random.uniform(1001.0, 5000.0)
        self.rand_execution_id = uuid.uuid4().hex
        self.rand_source = f"source_{uuid.uuid4().hex[:6]}"
        self.rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

    @patch('skills.anomaly_correlator.AnomalyDetector')
    @patch('skills.anomaly_correlator.AnomalyLogger')
    def test_correlator_initialization(self, mock_logger_cls, mock_detector_cls):
        detector_instance = mock_detector_cls.return_value
        logger_instance = mock_logger_cls.return_value

        correlator = AnomalyCorrelator(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_val
        )

        mock_detector_cls.assert_called_once_with(
            repo_path=self.rand_repo,
            threshold=self.rand_val,
            git_inspector=None,
            patch_verifier=None
        )
        mock_logger_cls.assert_called_once_with(log_path=self.rand_log)
        self.assertEqual(correlator.detector, detector_instance)
        self.assertEqual(correlator.logger, logger_instance)

    @patch('skills.anomaly_correlator.AnomalyDetector')
    @patch('skills.anomaly_correlator.AnomalyLogger')
    def test_correlate_metric_anomaly_detected(self, mock_logger_cls, mock_detector_cls):
        detector_instance = mock_detector_cls.return_value
        detector_instance.detect_anomaly.return_value = True
        logger_instance = mock_logger_cls.return_value

        correlator = AnomalyCorrelator(repo_path=self.rand_repo, log_path=self.rand_log)
        
        result = correlator.correlate_metric(self.rand_metric, self.rand_target)

        detector_instance.record_metric.assert_called_once_with(self.rand_metric, self.rand_target)
        detector_instance.detect_anomaly.assert_called_once_with(self.rand_metric, self.rand_target)
        logger_instance.log_anomaly.assert_called_once()
        
        args, kwargs = logger_instance.log_anomaly.call_args
        self.assertEqual(args[0], self.rand_metric)
        self.assertTrue(result)

    @patch('skills.anomaly_correlator.AnomalyDetector')
    @patch('skills.anomaly_correlator.AnomalyLogger')
    def test_correlate_metric_no_anomaly(self, mock_logger_cls, mock_detector_cls):
        detector_instance = mock_detector_cls.return_value
        detector_instance.detect_anomaly.return_value = False
        logger_instance = mock_logger_cls.return_value

        correlator = AnomalyCorrelator(repo_path=self.rand_repo, log_path=self.rand_log)
        
        result = correlator.correlate_metric(self.rand_metric, self.rand_target)

        detector_instance.record_metric.assert_called_once_with(self.rand_metric, self.rand_target)
        detector_instance.detect_anomaly.assert_called_once_with(self.rand_metric, self.rand_target)
        logger_instance.log_anomaly.assert_not_called()
        self.assertFalse(result)

    @patch('skills.anomaly_correlator.AnomalyDetector')
    @patch('skills.anomaly_correlator.AnomalyLogger')
    def test_analyze_execution_flow(self, mock_logger_cls, mock_detector_cls):
        detector_instance = mock_detector_cls.return_value
        rand_analysis_result = {uuid.uuid4().hex: random.randint(1, 100)}
        detector_instance.analyze_execution_metrics.return_value = rand_analysis_result
        
        logger_instance = mock_logger_cls.return_value

        correlator = AnomalyCorrelator(repo_path=self.rand_repo, log_path=self.rand_log)
        metrics_payload = {uuid.uuid4().hex: random.random()}

        result = correlator.analyze_execution_flow(self.rand_execution_id, metrics_payload)

        detector_instance.analyze_execution_metrics.assert_called_once_with(self.rand_execution_id, metrics_payload)
        self.assertEqual(result, rand_analysis_result)

    @patch('skills.anomaly_correlator.AnomalyDetector')
    @patch('skills.anomaly_correlator.AnomalyLogger')
    def test_get_correlation_report(self, mock_logger_cls, mock_detector_cls):
        logger_instance = mock_logger_cls.return_value
        rand_report = {uuid.uuid4().hex: uuid.uuid4().hex}
        logger_instance.get_structured_report.return_value = rand_report

        correlator = AnomalyCorrelator(repo_path=self.rand_repo, log_path=self.rand_log)
        report = correlator.get_correlation_report()

        logger_instance.get_structured_report.assert_called_once()
        self.assertEqual(report, rand_report)

    @patch('skills.anomaly_correlator.AnomalyDetector')
    @patch('skills.anomaly_correlator.AnomalyLogger')
    def test_correlate_metric_raises_custom_error(self, mock_logger_cls, mock_detector_cls):
        detector_instance = mock_detector_cls.return_value
        rand_error_msg = uuid.uuid4().hex
        detector_instance.detect_anomaly.side_effect = AnomalyDetectorError(rand_error_msg)

        correlator = AnomalyCorrelator(repo_path=self.rand_repo, log_path=self.rand_log)

        with self.assertRaises(AnomalyCorrelatorError) as ctx:
            correlator.correlate_metric(self.rand_metric, self.rand_target)
        
        self.assertIn(rand_error_msg, str(ctx.exception))


if __name__ == '__main__':
    unittest.main()