import unittest
from unittest.mock import MagicMock, patch
import random
import uuid

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.repo_id = uuid.uuid4().hex
        self.metric_name_1 = uuid.uuid4().hex
        self.metric_name_2 = uuid.uuid4().hex
        self.metric_name_3 = uuid.uuid4().hex

    def test_init_default_engine_and_logger(self):
        with patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine") as mock_engine_cls, \
             patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            
            mock_logger_cls.side_effect = TypeError("No args accepted")
            inspector = RepoHealthAnomalyInspector()
            
            mock_engine_cls.assert_called_once()
            mock_logger_cls.assert_called_once()
            self.assertIsNotNone(inspector.pulse_engine)
            self.assertIsNotNone(inspector.logger)

    def test_inspect_with_explicit_pulse_payload_no_anomalies(self):
        mock_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)

        val_normal = round(random.uniform(0.1, 50.0), 2)
        payload = {
            "metrics": {
                self.metric_name_1: val_normal
            }
        }

        result = inspector.inspect(repo_id=self.repo_id, pulse_payload=payload, threshold=100.0)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)
        mock_engine.get_pulse.assert_not_called()
        mock_engine.pulse.assert_not_called()

    def test_inspect_fetches_pulse_via_get_pulse(self):
        mock_engine = MagicMock()
        del mock_engine.pulse
        val_high = round(random.uniform(105.0, 200.0), 2)
        threshold = 100.0
        mock_engine.get_pulse.return_value = {
            "metrics": {
                self.metric_name_1: val_high
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(repo_id=self.repo_id, threshold=threshold)

        mock_engine.get_pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.metric_name_1)
        self.assertEqual(result["anomalies"][0]["deviation"], "high")
        self.assertEqual(result["deviation_score"], val_high - threshold)

    def test_inspect_fetches_pulse_via_pulse_method(self):
        mock_engine = MagicMock()
        if hasattr(mock_engine, "get_pulse"):
            del mock_engine.get_pulse
        
        val_negative = -round(random.uniform(1.0, 50.0), 2)
        mock_engine.pulse.return_value = {
            "metrics": {
                self.metric_name_2: val_negative
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(repo_id=self.repo_id)

        mock_engine.pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.metric_name_2)
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")
        self.assertEqual(result["deviation_score"], abs(val_negative))

    def test_inspect_fallback_empty_pulse(self):
        mock_engine = MagicMock()
        if hasattr(mock_engine, "get_pulse"):
            del mock_engine.get_pulse
        if hasattr(mock_engine, "pulse"):
            del mock_engine.pulse

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(repo_id=self.repo_id)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_multiple_anomalies_and_mixed_metrics(self):
        mock_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)

        val_negative = -round(random.uniform(1.0, 10.0), 2)
        val_high = round(random.uniform(150.0, 300.0), 2)
        val_normal = round(random.uniform(10.0, 50.0), 2)
        val_string = uuid.uuid4().hex
        threshold = 100.0

        payload = {
            "metrics": {
                self.metric_name_1: val_negative,
                self.metric_name_2: val_high,
                self.metric_name_3: val_normal,
                uuid.uuid4().hex: val_string
            }
        }

        result = inspector.inspect(repo_id=self.repo_id, pulse_payload=payload, threshold=threshold)

        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 2)
        
        expected_deviation_score = abs(val_negative) + (val_high - threshold)
        self.assertAlmostEqual(result["deviation_score"], expected_deviation_score, places=5)
        
        anomaly_metrics = {a["metric"] for a in result["anomalies"]}
        self.assertIn(self.metric_name_1, anomaly_metrics)
        self.assertIn(self.metric_name_2, anomaly_metrics)
        self.assertNotIn(self.metric_name_3, anomaly_metrics)


if __name__ == "__main__":
    unittest.main()