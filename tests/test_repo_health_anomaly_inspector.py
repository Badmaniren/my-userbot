import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector

class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.repo_id = uuid.uuid4().hex
        self.metric_name_1 = uuid.uuid4().hex
        self.metric_name_2 = uuid.uuid4().hex
        self.metric_name_3 = uuid.uuid4().hex

    def test_init_default_engines(self):
        with patch('skills.repo_health_anomaly_inspector.RepoHealthPulseEngine') as mock_pulse_engine, \
             patch('skills.repo_health_anomaly_inspector.RepoLogger') as mock_logger:
            
            inspector = RepoHealthAnomalyInspector()
            mock_pulse_engine.assert_called_once()
            mock_logger.assert_called()
            self.assertIsNotNone(inspector.pulse_engine)
            self.assertIsNotNone(inspector.logger)

    def test_inspect_with_provided_pulse_payload(self):
        negative_val = -float(random.randint(1, 100))
        high_val = float(random.randint(150, 300))
        normal_val = float(random.randint(1, 50))
        threshold = 100.0

        pulse_payload = {
            "metrics": {
                self.metric_name_1: negative_val,
                self.metric_name_2: high_val,
                self.metric_name_3: normal_val
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=MagicMock())
        result = inspector.inspect(self.repo_id, pulse_payload=pulse_payload, threshold=threshold)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 2)
        
        expected_deviation_score = abs(negative_val) + (high_val - threshold)
        self.assertAlmostEqual(result["deviation_score"], expected_deviation_score)

        anomaly_metrics = [a["metric"] for a in result["anomalies"]]
        self.assertIn(self.metric_name_1, anomaly_metrics)
        self.assertIn(self.metric_name_2, anomaly_metrics)
        self.assertNotIn(self.metric_name_3, anomaly_metrics)

    def test_inspect_fetches_via_get_pulse(self):
        mock_engine = MagicMock()
        negative_val = -float(random.randint(1, 50))
        mock_engine.get_pulse.return_value = {
            "metrics": {
                self.metric_name_1: negative_val
            }
        }
        del mock_engine.pulse

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.repo_id)

        mock_engine.get_pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["deviation_score"], abs(negative_val))

    def test_inspect_fetches_via_pulse(self):
        mock_engine = MagicMock()
        del mock_engine.get_pulse
        high_val = float(random.randint(200, 500))
        threshold = 150.0
        mock_engine.pulse.return_value = {
            "metrics": {
                self.metric_name_1: high_val
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.repo_id, threshold=threshold)

        mock_engine.pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertAlmostEqual(result["deviation_score"], high_val - threshold)

    def test_inspect_fallback_empty_payload(self):
        mock_engine = MagicMock()
        if hasattr(mock_engine, "get_pulse"):
            del mock_engine.get_pulse
        if hasattr(mock_engine, "pulse"):
            del mock_engine.pulse

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(self.repo_id)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_no_anomalies_normal_metrics(self):
        normal_val_1 = float(random.randint(1, 40))
        normal_val_2 = float(random.randint(41, 80))
        threshold = 100.0

        pulse_payload = {
            "metrics": {
                self.metric_name_1: normal_val_1,
                self.metric_name_2: normal_val_2
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=MagicMock())
        result = inspector.inspect(self.repo_id, pulse_payload=pulse_payload, threshold=threshold)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 0)
        self.assertEqual(result["deviation_score"], 0.0)

if __name__ == '__main__':
    unittest.main()