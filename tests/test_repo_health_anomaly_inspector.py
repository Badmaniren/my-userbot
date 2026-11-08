import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector

class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.repo_id = uuid.uuid4().hex
        self.metric_name_neg = uuid.uuid4().hex
        self.metric_name_high = uuid.uuid4().hex
        self.metric_name_normal = uuid.uuid4().hex

    def test_init_logger_resilience(self):
        with patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            mock_logger_cls.side_effect = TypeError("Missing positional argument")
            inspector = RepoHealthAnomalyInspector()
            mock_logger_cls.assert_called_with()
            self.assertIsNotNone(inspector)

    def test_inspect_with_explicit_payload(self):
        negative_val = -float(random.randint(1, 100))
        high_val = float(random.randint(100, 1000))
        normal_val = float(random.randint(0, 50))
        threshold = 50.0

        payload = {
            "metrics": {
                self.metric_name_neg: negative_val,
                self.metric_name_high: high_val,
                self.metric_name_normal: normal_val
            }
        }

        inspector = RepoHealthAnomalyInspector()
        result = inspector.inspect(repo_id=self.repo_id, pulse_payload=payload, threshold=threshold)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        
        anomalies = result["anomalies"]
        self.assertEqual(len(anomalies), 2)

        metric_deviations = {a["metric"]: a for a in anomalies}
        self.assertIn(self.metric_name_neg, metric_deviations)
        self.assertEqual(metric_deviations[self.metric_name_neg]["deviation"], "negative")
        self.assertEqual(metric_deviations[self.metric_name_neg]["value"], negative_val)

        self.assertIn(self.metric_name_high, metric_deviations)
        self.assertEqual(metric_deviations[self.metric_name_high]["deviation"], "high")
        self.assertEqual(metric_deviations[self.metric_name_high]["value"], high_val)

        expected_deviation_score = abs(negative_val) + (high_val - threshold)
        self.assertAlmostEqual(result["deviation_score"], expected_deviation_score)

    def test_inspect_fetches_pulse_via_get_pulse(self):
        mock_engine = MagicMock()
        negative_val = -float(random.randint(1, 50))
        mock_engine.get_pulse.return_value = {
            "metrics": {
                self.metric_name_neg: negative_val
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(repo_id=self.repo_id)

        mock_engine.get_pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertEqual(len(result["anomalies"]), 1)

    def test_inspect_fetches_pulse_via_pulse_fallback(self):
        mock_engine = MagicMock(spec=["pulse"])
        mock_engine.pulse = MagicMock(return_value={
            "metrics": {
                self.metric_name_normal: float(random.randint(1, 10))
            }
        })

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(repo_id=self.repo_id, threshold=100.0)

        mock_engine.pulse.assert_called_once_with(self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_empty_payload_or_missing_methods(self):
        mock_engine = MagicMock(spec=[])
        if hasattr(mock_engine, "get_pulse"):
            del mock_engine.get_pulse
        if hasattr(mock_engine, "pulse"):
            del mock_engine.pulse

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)

        result_none = inspector.inspect(repo_id=self.repo_id, pulse_payload=None)
        self.assertFalse(result_none["is_anomaly"])
        self.assertEqual(result_none["anomalies"], [])
        self.assertEqual(result_none["deviation_score"], 0.0)

        result_empty_dict = inspector.inspect(repo_id=self.repo_id, pulse_payload={})
        self.assertFalse(result_empty_dict["is_anomaly"])

    def test_inspect_ignores_non_numeric_metrics(self):
        string_val = uuid.uuid4().hex
        payload = {
            "metrics": {
                self.metric_name_normal: string_val,
                self.metric_name_high: None
            }
        }

        inspector = RepoHealthAnomalyInspector()
        result = inspector.inspect(repo_id=self.repo_id, pulse_payload=payload, threshold=10.0)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)