import unittest
from unittest.mock import patch
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def test_init_default_engine_and_logger(self):
        with patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            mock_logger_cls.side_effect = TypeError("No args accepted")
            with patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine") as mock_engine_cls:
                inspector = RepoHealthAnomalyInspector()
                self.assertIsNotNone(inspector)
                mock_logger_cls.assert_any_call()

    def test_inspect_with_custom_pulse_payload_negative_anomaly(self):
        repo_id = uuid.uuid4().hex
        metric_name = uuid.uuid4().hex
        negative_value = -float(random.randint(1, 100))
        
        payload = {
            "metrics": {
                metric_name: negative_value
            }
        }
        
        inspector = RepoHealthAnomalyInspector()
        result = inspector.inspect(repo_id, pulse_payload=payload)
        
        self.assertEqual(result["repo_id"], repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], metric_name)
        self.assertEqual(result["anomalies"][0]["value"], negative_value)
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")
        self.assertEqual(result["deviation_score"], abs(negative_value))

    def test_inspect_with_threshold_anomaly(self):
        repo_id = uuid.uuid4().hex
        metric_name = uuid.uuid4().hex
        threshold = float(random.randint(10, 50))
        high_value = threshold + float(random.randint(1, 50))
        
        payload = {
            "metrics": {
                metric_name: high_value
            }
        }
        
        inspector = RepoHealthAnomalyInspector()
        result = inspector.inspect(repo_id, pulse_payload=payload, threshold=threshold)
        
        self.assertEqual(result["repo_id"], repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], metric_name)
        self.assertEqual(result["anomalies"][0]["value"], high_value)
        self.assertEqual(result["anomalies"][0]["deviation"], "high")
        self.assertEqual(result["deviation_score"], high_value - threshold)

    def test_inspect_fallback_to_pulse_engine_get_pulse(self):
        repo_id = uuid.uuid4().hex
        metric_name = uuid.uuid4().hex
        negative_value = -float(random.randint(1, 50))
        
        mock_engine = unittest.mock.MagicMock()
        mock_engine.get_pulse.return_value = {
            "metrics": {
                metric_name: negative_value
            }
        }
        del mock_engine.pulse

        inspector = RepoHealthPulseEngine = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(repo_id)

        mock_engine.get_pulse.assert_called_once_with(repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["anomalies"][0]["value"], negative_value)

    def test_inspect_fallback_to_pulse_engine_pulse(self):
        repo_id = uuid.uuid4().hex
        metric_name = uuid.uuid4().hex
        negative_value = -float(random.randint(1, 50))
        
        mock_engine = unittest.mock.MagicMock()
        del mock_engine.get_pulse
        mock_engine.pulse.return_value = {
            "metrics": {
                metric_name: negative_value
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(repo_id)

        mock_engine.pulse.assert_called_once_with(repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["anomalies"][0]["value"], negative_value)


class TestRepoHealthAnomalyInspectorIntegration(unittest.TestCase):

    def test_anomaly_inspector_integration_with_pulse_engine(self):
        repo_id = uuid.uuid4().hex
        metric_name = uuid.uuid4().hex
        bad_value = -float(random.randint(100, 999))

        with patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine") as mock_engine_cls:
            mock_instance = mock_engine_cls.return_value
            mock_instance.get_pulse.return_value = {
                "metrics": {
                    metric_name: bad_value
                }
            }

            inspector = RepoHealthAnomalyInspector()
            result = inspector.inspect(repo_id)

            self.assertTrue(result["is_anomaly"])
            self.assertEqual(result["repo_id"], repo_id)
            self.assertEqual(len(result["anomalies"]), 1)
            self.assertEqual(result["anomalies"][0]["value"], bad_value)
            self.assertGreater(result["deviation_score"], 0.0)