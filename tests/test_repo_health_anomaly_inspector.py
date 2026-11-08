import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):
    def setUp(self):
        self.repo_id = str(uuid.uuid4())
        self.metric_name_neg = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.metric_name_high = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.metric_name_normal = ''.join(random.choices(string.ascii_lowercase, k=10))

    @patch("skills.repo_health_anomaly_inspector.RepoLogger")
    @patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine")
    def test_init_default_engines(self, mock_pulse_engine_class, mock_repo_logger_class):
        inspector = RepoHealthAnomalyInspector()
        self.assertIsNotNone(inspector.pulse_engine)
        self.assertIsNotNone(inspector.logger)
        mock_pulse_engine_class.assert_called_once()
        mock_repo_logger_class.assert_called()

    @patch("skills.repo_health_anomaly_inspector.RepoLogger")
    def test_init_custom_pulse_engine(self, mock_repo_logger_class):
        custom_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=custom_engine)
        self.assertEqual(inspector.pulse_engine, custom_engine)

    def test_inspect_with_explicit_pulse_payload_negative_anomaly(self):
        negative_value = -float(random.randint(1, 100))
        payload = {
            "metrics": {
                self.metric_name_neg: negative_value,
                self.metric_name_normal: random.randint(0, 50)
            }
        }
        mock_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)

        result = inspector.inspect(repo_id=self.repo_id, pulse_payload=payload)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.metric_name_neg)
        self.assertEqual(result["anomalies"][0]["value"], negative_value)
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")
        self.assertEqual(result["deviation_score"], abs(negative_value))
        mock_engine.get_pulse.assert_not_called()

    def test_inspect_with_explicit_pulse_payload_high_anomaly(self):
        threshold = float(random.randint(10, 50))
        high_value = threshold + float(random.randint(1, 50))
        payload = {
            "metrics": {
                self.metric_name_high: high_value,
                self.metric_name_normal: threshold / 2
            }
        }
        mock_engine = MagicMock()
        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)

        result = inspector.inspect(repo_id=self.repo_id, pulse_payload=payload, threshold=threshold)

        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.metric_name_high)
        self.assertEqual(result["anomalies"][0]["value"], high_value)
        self.assertEqual(result["anomalies"][0]["deviation"], "high")
        self.assertEqual(result["deviation_score"], high_value - threshold)

    def test_inspect_fetches_pulse_via_get_pulse(self):
        negative_value = -float(random.randint(1, 100))
        mock_engine = MagicMock()
        mock_engine.get_pulse.return_value = {
            "metrics": {
                self.metric_name_neg: negative_value
            }
        }
        del mock_engine.pulse

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(repo_id=self.repo_id)

        mock_engine.get_pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["deviation_score"], abs(negative_value))

    def test_inspect_fetches_pulse_via_pulse_method(self):
        threshold = float(random.randint(5, 20))
        high_value = threshold + float(random.randint(5, 20))
        mock_engine = MagicMock()
        del mock_engine.get_pulse
        mock_engine.pulse.return_value = {
            "metrics": {
                self.metric_name_high: high_value
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(repo_id=self.repo_id, threshold=threshold)

        mock_engine.pulse.assert_called_once_with(self.repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["deviation_score"], high_value - threshold)

    def test_inspect_pulse_engine_no_matching_methods(self):
        mock_engine = object()
        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(repo_id=self.repo_id)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_pulse_payload_is_none_fallback(self):
        mock_engine = MagicMock()
        mock_engine.get_pulse.return_value = None

        inspector = RepoHealthAnomalyInspector(pulse_engine=mock_engine)
        result = inspector.inspect(repo_id=self.repo_id)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_no_anomalies_normal_metrics(self):
        threshold = float(random.randint(100, 200))
        normal_value = float(random.randint(1, 50))
        payload = {
            "metrics": {
                self.metric_name_normal: normal_value,
                "another_metric": threshold
            }
        }
        inspector = RepoHealthAnomalyInspector(pulse_engine=MagicMock())
        result = inspector.inspect(repo_id=self.repo_id, pulse_payload=payload, threshold=threshold)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_ignores_non_numeric_metrics(self):
        string_metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        payload = {
            "metrics": {
                string_metric_name: ''.join(random.choices(string.ascii_letters, k=12))
            }
        }
        inspector = RepoHealthAnomalyInspector(pulse_engine=MagicMock())
        result = inspector.inspect(repo_id=self.repo_id, pulse_payload=payload, threshold=10.0)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)


if __name__ == '__main__':
    unittest.main()