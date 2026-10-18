import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.anomaly_correlator import AnomalyCorrelator, AnomalyCorrelatorError
from skills.anomaly_detector import AnomalyDetectorError


class TestAnomalyCorrelatorInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path_mock = f"/repo_{uuid.uuid4().hex}"
        self.log_path_mock = f"/log_{uuid.uuid4().hex}.log"
        self.threshold_mock = random.uniform(10.0, 100.0)

    @patch('skills.anomaly_correlator.AnomalyDetector')
    @patch('skills.anomaly_correlator.AnomalyLogger')
    def test_init_default_and_custom_inject(self, mock_logger_cls, mock_detector_cls):
        custom_detector = MagicMock()
        custom_logger = MagicMock()
        
        correlator = AnomalyCorrelator(
            repo_path=self.repo_path_mock,
            log_path=self.log_path_mock,
            threshold=self.threshold_mock,
            detector=custom_detector,
            logger=custom_logger
        )
        
        self.assertEqual(correlator.detector, custom_detector)
        self.assertEqual(correlator.logger, custom_logger)
        mock_detector_cls.assert_not_called()
        mock_logger_cls.assert_not_called()

        correlator_default = AnomalyCorrelator(
            repo_path=self.repo_path_mock,
            log_path=self.log_path_mock,
            threshold=self.threshold_mock
        )
        mock_detector_cls.assert_called_once()
        mock_logger_cls.assert_called_once_with(log_path=self.log_path_mock)

    @patch('skills.anomaly_correlator.AnomalyDetector')
    @patch('skills.anomaly_correlator.AnomalyLogger')
    def test_correlate_metric_anomaly_detected(self, mock_logger_cls, mock_detector_cls):
        metric_name = f"metric_{uuid.uuid4().hex}"
        metric_value = random.uniform(100.0, 500.0)

        detector_instance = mock_detector_cls.return_value
        detector_instance.detect_anomaly.return_value = True

        logger_instance = mock_logger_cls.return_value

        correlator = AnomalyCorrelator(repo_path=self.repo_path_mock)
        result = correlator.correlate_metric(metric_name, metric_value)

        self.assertTrue(result)
        detector_instance.record_metric.assert_called_once_with(metric_name, metric_value)
        detector_instance.detect_anomaly.assert_called_once_with(metric_name, metric_value)
        logger_instance.log_anomaly.assert_called_once_with(metric_name)

    @patch('skills.anomaly_correlator.AnomalyDetector')
    @patch('skills.anomaly_correlator.AnomalyLogger')
    def test_correlate_metric_no_anomaly(self, mock_logger_cls, mock_detector_cls):
        metric_name = f"metric_{uuid.uuid4().hex}"
        metric_value = random.uniform(0.0, 10.0)

        detector_instance = mock_detector_cls.return_value
        detector_instance.detect_anomaly.return_value = False
        logger_instance = mock_logger_cls.return_value

        correlator = AnomalyCorrelator(repo_path=self.repo_path_mock)
        result = correlator.correlate_metric(metric_name, metric_value)

        self.assertFalse(result)
        detector_instance.record_metric.assert_called_once_with(metric_name, metric_value)
        detector_instance.detect_anomaly.assert_called_once_with(metric_name, metric_value)
        logger_instance.log_anomaly.assert_not_called()

    @patch('skills.anomaly_correlator.AnomalyDetector')
    @patch('skills.anomaly_correlator.AnomalyLogger')
    def test_correlate_metric_detector_error(self, mock_logger_cls, mock_detector_cls):
        metric_name = f"metric_{uuid.uuid4().hex}"
        metric_value = random.uniform(50.0, 150.0)
        error_msg = f"detector_failure_{uuid.uuid4().hex}"

        detector_instance = mock_detector_cls.return_value
        detector_instance.record_metric.side_effect = AnomalyDetectorError(error_msg)

        correlator = AnomalyCorrelator(repo_path=self.repo_path_mock)
        with self.assertRaises(AnomalyCorrelatorError) as ctx:
            correlator.correlate_metric(metric_name, metric_value)

        self.assertIn(error_msg, str(ctx.exception))

    @patch('skills.anomaly_correlator.AnomalyDetector')
    @patch('skills.anomaly_correlator.AnomalyLogger')
    def test_analyze_execution_flow(self, mock_logger_cls, mock_detector_cls):
        execution_id = uuid.uuid4().hex
        metrics_payload = {f"metric_{uuid.uuid4().hex}": random.randint(1, 100)}
        expected_analysis = {uuid.uuid4().hex: random.random()}

        detector_instance = mock_detector_cls.return_value
        detector_instance.analyze_execution_metrics.return_value = expected_analysis

        correlator = AnomalyCorrelator(repo_path=self.repo_path_mock)
        result = correlator.analyze_execution_flow(execution_id, metrics_payload)

        self.assertEqual(result, expected_analysis)
        detector_instance.analyze_execution_metrics.assert_called_once_with(execution_id, metrics_payload)

    @patch('skills.anomaly_correlator.AnomalyDetector')
    @patch('skills.anomaly_correlator.AnomalyLogger')
    def test_get_correlation_report(self, mock_logger_cls, mock_detector_cls):
        expected_report = {uuid.uuid4().hex: uuid.uuid4().hex}
        logger_instance = mock_logger_cls.return_value
        logger_instance.get_structured_report.return_value = expected_report

        correlator = AnomalyCorrelator(repo_path=self.repo_path_mock)
        report = correlator.get_correlation_report()

        self.assertEqual(report, expected_report)
        logger_instance.get_structured_report.assert_called_once()

    @patch('skills.anomaly_correlator.AnomalyDetector')
    @patch('skills.anomaly_correlator.AnomalyLogger')
    def test_correlate_events(self, mock_logger_cls, mock_detector_cls):
        anomalies_mock = [uuid.uuid4().hex, uuid.uuid4().hex]
        report_mock = {uuid.uuid4().hex: random.randint(10, 50)}

        logger_instance = mock_logger_cls.return_value
        logger_instance.get_anomalies.return_value = anomalies_mock
        logger_instance.get_structured_report.return_value = report_mock

        correlator = AnomalyCorrelator(repo_path=self.repo_path_mock)
        res = correlator.correlate_events()

        self.assertEqual(res["correlated_count"], len(anomalies_mock))
        self.assertEqual(res["report"], report_mock)
        logger_instance.get_anomalies.assert_called_once()
        logger_instance.get_structured_report.assert_called_once()


if __name__ == '__main__':
    unittest.main()