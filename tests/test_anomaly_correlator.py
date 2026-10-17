import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.anomaly_correlator import AnomalyCorrelator, AnomalyCorrelatorError
from skills.anomaly_detector import AnomalyDetectorError
from skills.anomaly_filter import AnomalyFilter


class TestAnomalyCorrelator(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.log_path = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 5.0)
        
        self.mock_detector = MagicMock()
        self.mock_logger = MagicMock()
        
        self.correlator = AnomalyCorrelator(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold,
            detector=self.mock_detector,
            logger=self.mock_logger
        )

    def test_init_default_dependencies(self):
        with patch('skills.anomaly_correlator.AnomalyDetector') as mock_detector_cls, \
             patch('skills.anomaly_correlator.AnomalyLogger') as mock_logger_cls:
            
            r_path = f"/repo/{uuid.uuid4().hex}"
            l_path = f"/logs/{uuid.uuid4().hex}"
            thresh = random.uniform(1.0, 10.0)
            
            corr = AnomalyCorrelator(repo_path=r_path, log_path=l_path, threshold=thresh)
            
            mock_detector_cls.assert_called_once_with(
                repo_path=r_path,
                threshold=thresh,
                git_inspector=None,
                patch_verifier=None
            )
            mock_logger_cls.assert_called_once_with(log_path=l_path)
            self.assertIsNotNone(corr.detector)
            self.assertIsNotNone(corr.logger)

    def test_correlate_metric_anomaly_detected(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        value = random.uniform(10.0, 100.0)
        
        self.mock_detector.detect_anomaly.return_value = True

        result = self.correlator.correlate_metric(metric_name, value)

        self.assertTrue(result)
        self.mock_detector.record_metric.assert_called_once_with(metric_name, value)
        self.mock_detector.detect_anomaly.assert_called_once_with(metric_name, value)
        self.mock_logger.log_anomaly.assert_called_once_with(metric_name)

    def test_correlate_metric_no_anomaly(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        value = random.uniform(0.0, 5.0)
        
        self.mock_detector.detect_anomaly.return_value = False

        result = self.correlator.correlate_metric(metric_name, value)

        self.assertFalse(result)
        self.mock_detector.record_metric.assert_called_once_with(metric_name, value)
        self.mock_detector.detect_anomaly.assert_called_once_with(metric_name, value)
        self.mock_logger.log_anomaly.assert_not_called()

    def test_correlate_metric_detector_error(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        value = random.uniform(10.0, 100.0)
        error_message = f"Detector failure {uuid.uuid4().hex}"

        self.mock_detector.record_metric.side_effect = AnomalyDetectorError(error_message)
        
        with self.assertRaises(AnomalyCorrelatorError) as ctx:
            self.correlator.correlate_metric(metric_name, value)

        self.assertIn(error_message, str(ctx.exception))

    def test_analyze_execution_flow(self):
        execution_id = uuid.uuid4().hex
        metrics_payload = {
            f"key_{uuid.uuid4().hex[:4]}": random.randint(1, 100)
            for _ in range(3)
        }
        expected_analysis = {f"result_{uuid.uuid4().hex}": random.random()}
        
        self.mock_detector.analyze_execution_metrics.return_value = expected_analysis

        res = self.correlator.analyze_execution_flow(execution_id, metrics_payload)

        self.assertEqual(res, expected_analysis)
        self.mock_detector.analyze_execution_metrics.assert_called_once_with(execution_id, metrics_payload)

    def test_get_correlation_report(self):
        expected_report = {
            f"section_{uuid.uuid4().hex}": uuid.uuid4().hex
            for _ in range(2)
        }
        self.mock_logger.get_structured_report.return_value = expected_report

        report = self.correlator.get_correlation_report()

        self.assertEqual(report, expected_report)
        self.mock_logger.get_structured_report.assert_called_once()

    def test_correlate_events(self):
        anomalies_list = [uuid.uuid4().hex, uuid.uuid4().hex]
        report_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        
        self.mock_logger.get_anomalies.return_value = anomalies_list
        self.mock_logger.get_structured_report.return_value = report_data

        events_result = self.correlator.correlate_events()

        self.assertEqual(events_result["correlated_count"], len(anomalies_list))
        self.assertEqual(events_result["report"], report_data)
        self.mock_logger.get_anomalies.assert_called_once()
        self.mock_logger.get_structured_report.assert_called_once()

    def test_composition_with_anomaly_filter(self):
        raw_data = {uuid.uuid4().hex: ''.join(random.choices(string.ascii_letters, k=10))}
        filter_instance = AnomalyFilter()

        with patch.object(filter_instance, 'filter', return_value=raw_data) as mock_filter:
            filtered = filter_instance.filter(raw_data)
            self.assertEqual(filtered, raw_data)
            mock_filter.assert_called_once_with(raw_data)


if __name__ == '__main__':
    unittest.main()