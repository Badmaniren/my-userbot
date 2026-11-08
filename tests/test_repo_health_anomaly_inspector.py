import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector, AnomalyInspector

class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.repo_id = str(uuid.uuid4())
        self.metric_name_neg = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.metric_name_high = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.metric_name_normal = ''.join(random.choices(string.ascii_lowercase, k=8))

    def test_init_default_pulse_engine(self):
        with patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine") as mock_engine_cls, \
             patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            
            inspector = RepoHealthAnomalyInspector()
            self.assertIsNotNone(inspector.pulse_engine)
            mock_engine_cls.assert_called_once()

    def test_inspect_fetches_pulse_when_payload_is_none(self):
        mock_pulse_engine = MagicMock()
        negative_val = -float(random.randint(1, 100))
        mock_pulse_engine.get_pulse.return_value = {
            "metrics": {
                self.metric_name_neg: negative_val
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(self.repo_id)

        mock_pulse_engine.get_pulse.assert_called_once_with(self.repo_id)
        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.metric_name_neg)
        self.assertEqual(result["anomalies"][0]["value"], negative_val)
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")
        self.assertEqual(result["deviation_score"], abs(negative_val))

    def test_inspect_falls_back_to_pulse_method(self):
        mock_pulse_engine = MagicMock(spec=[])
        del mock_pulse_engine.get_pulse
        mock_pulse_engine.pulse = MagicMock(return_value={"metrics": {}})

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(self.repo_id)

        mock_pulse_engine.pulse.assert_called_once_with(self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_anomaly_inspector_stream_inspection(self):
        self.assertTrue(issubclass(AnomalyInspector, RepoHealthAnomalyInspector))
        inspector = AnomalyInspector(threshold_cpu=80.0, threshold_error=5.0)

        stream = [
            {"metric_id": "normal-1", "cpu_load": 25.0, "error_rate": 0.1, "timestamp": "2026-11-08T00:00:00"},
            {"metric_id": "anomaly-cpu", "cpu_load": 95.0, "error_rate": 1.0, "timestamp": "2026-11-08T01:00:00"},
            {"metric_id": "anomaly-err", "cpu_load": 20.0, "error_rate": 12.0, "timestamp": "2026-11-08T02:00:00"},
            {"metric_id": "normal-2", "cpu_load": 40.0, "error_rate": 2.0, "timestamp": "2026-11-08T03:00:00"}
        ]

        anomalies = inspector.inspect(stream)
        self.assertEqual(len(anomalies), 2)
        anomaly_ids = [a["metric_id"] for a in anomalies]
        self.assertIn("anomaly-cpu", anomaly_ids)
        self.assertIn("anomaly-err", anomaly_ids)
        self.assertNotIn("normal-1", anomaly_ids)
        self.assertNotIn("normal-2", anomaly_ids)

    def test_inspect_with_explicit_pulse_payload_and_threshold(self):
        mock_pulse_engine = MagicMock()
        threshold_val = float(random.randint(50, 100))
        high_val = threshold_val + float(random.randint(10, 50))
        normal_val = threshold_val - float(random.randint(1, 40))

        payload = {
            "metrics": {
                self.metric_name_high: high_val,
                self.metric_name_normal: normal_val
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(self.repo_id, pulse_payload=payload, threshold=threshold_val)

        mock_pulse_engine.get_pulse.assert_not_called()
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.metric_name_high)
        self.assertEqual(result["anomalies"][0]["value"], high_val)
        self.assertEqual(result["anomalies"][0]["deviation"], "high")
        self.assertEqual(result["deviation_score"], high_val - threshold_val)

    def test_inspect_with_negative_and_high_anomalies(self):
        mock_pulse_engine = MagicMock()
        negative_val = -float(random.randint(1, 50))
        threshold_val = float(random.randint(50, 100))
        high_val = threshold_val + float(random.randint(10, 50))

        payload = {
            "metrics": {
                self.metric_name_neg: negative_val,
                self.metric_name_high: high_val
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(self.repo_id, pulse_payload=payload, threshold=threshold_val)

        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 2)
        
        expected_deviation_score = abs(negative_val) + (high_val - threshold_val)
        self.assertEqual(result["deviation_score"], expected_deviation_score)

    def test_inspect_empty_pulse_payload(self):
        mock_pulse_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        
        result = inspector.inspect(self.repo_id, pulse_payload={})
        
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_none_pulse_payload_handled(self):
        mock_pulse_engine = MagicMock()
        mock_pulse_engine.get_pulse.return_value = None

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_pulse_engine)
        result = inspector.inspect(self.repo_id)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)