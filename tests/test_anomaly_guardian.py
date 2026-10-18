import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.anomaly_guardian import AnomalyGuardian, AnomalyGuardianError
from skills.anomaly_detector import AnomalyDetector, AnomalyDetectorError
from skills.anomaly_reactor import AutonomousReactorEngine


class TestAnomalyGuardian(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.threshold = random.uniform(0.1, 0.9)
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.target_value = random.uniform(1.0, 100.0)
        self.execution_id = uuid.uuid4().hex

    def test_guardian_initialization_and_composition(self):
        with patch('skills.anomaly_guardian.AnomalyDetector') as mock_detector_cls, \
             patch('skills.anomaly_guardian.AutonomousReactorEngine') as mock_reactor_cls, \
             patch('skills.anomaly_guardian.GitInspector') as mock_git_cls, \
             patch('skills.anomaly_guardian.PatchVerifier') as mock_verifier_cls:

            mock_detector_instance = mock_detector_cls.return_value
            mock_reactor_instance = mock_reactor_cls.return_value

            guardian = AnomalyGuardian(repo_path=self.repo_path, threshold=self.threshold)

            mock_detector_cls.assert_called_once()
            mock_reactor_cls.assert_called_once()
            self.assertEqual(guardian.detector, mock_detector_instance)
            self.assertEqual(guardian.reactor, mock_reactor_instance)

    def test_record_metric_delegation(self):
        with patch('skills.anomaly_guardian.AnomalyDetector') as mock_detector_cls, \
             patch('skills.anomaly_guardian.AutonomousReactorEngine'):

            mock_detector = mock_detector_cls.return_value
            guardian = AnomalyGuardian(repo_path=self.repo_path, threshold=self.threshold)

            val = random.uniform(0.0, 50.0)
            guardian.record_metric(self.metric_name, val)

            mock_detector.record_metric.assert_called_once_with(self.metric_name, val)

    def test_guard_execution_no_anomaly(self):
        with patch('skills.anomaly_guardian.AnomalyDetector') as mock_detector_cls, \
             patch('skills.anomaly_guardian.AutonomousReactorEngine') as mock_reactor_cls:

            mock_detector = mock_detector_cls.return_value
            mock_reactor = mock_reactor_cls.return_value

            mock_detector.detect_anomaly.return_value = False

            guardian = AnomalyGuardian(repo_path=self.repo_path, threshold=self.threshold)
            result = guardian.guard_execution(self.metric_name, self.target_value)

            mock_detector.detect_anomaly.assert_called_once_with(self.metric_name, self.target_value)
            mock_reactor.handle_anomaly.assert_not_called()
            self.assertFalse(result)

    def test_guard_execution_with_anomaly_triggers_reactor(self):
        with patch('skills.anomaly_guardian.AnomalyDetector') as mock_detector_cls, \
             patch('skills.anomaly_guardian.AutonomousReactorEngine') as mock_reactor_cls:

            mock_detector = mock_detector_cls.return_value
            mock_reactor = mock_reactor_cls.return_value

            mock_detector.detect_anomaly.return_value = True

            guardian = AnomalyGuardian(repo_path=self.repo_path, threshold=self.threshold)
            result = guardian.guard_execution(self.metric_name, self.target_value)

            mock_detector.detect_anomaly.assert_called_once_with(self.metric_name, self.target_value)
            mock_reactor.handle_anomaly.assert_called_once()
            self.assertTrue(result)

    def test_analyze_and_suppress_batch(self):
        with patch('skills.anomaly_guardian.AnomalyDetector') as mock_detector_cls, \
             patch('skills.anomaly_guardian.AutonomousReactorEngine') as mock_reactor_cls:

            mock_detector = mock_detector_cls.return_value
            mock_reactor = mock_reactor_cls.return_value

            analysis_result = {
                uuid.uuid4().hex: True,
                uuid.uuid4().hex: random.choice([True, False])
            }
            mock_detector.analyze_execution_metrics.return_value = analysis_result

            metrics_payload = {uuid.uuid4().hex: random.randint(1, 100)}

            guardian = AnomalyGuardian(repo_path=self.repo_path, threshold=self.threshold)
            res = guardian.analyze_and_suppress(self.execution_id, metrics_payload)

            mock_detector.analyze_execution_metrics.assert_called_once_with(self.execution_id, metrics_payload)
            mock_reactor.handle_anomaly.assert_called()
            self.assertEqual(res, analysis_result)

    def test_guardian_raises_custom_error_on_detector_failure(self):
        with patch('skills.anomaly_guardian.AnomalyDetector') as mock_detector_cls, \
             patch('skills.anomaly_guardian.AutonomousReactorEngine'):

            mock_detector = mock_detector_cls.return_value
            err_msg = uuid.uuid4().hex
            mock_detector.detect_anomaly.side_effect = AnomalyDetectorError(err_msg)

            guardian = AnomalyGuardian(repo_path=self.repo_path, threshold=self.threshold)

            with self.assertRaises(AnomalyGuardianError):
                guardian.guard_execution(self.metric_name, self.target_value)