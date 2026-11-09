import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.rand_repo_id = uuid.uuid4().hex
        self.pulse_engine_mock = MagicMock()
        self.inspector = RepoHealthAnomalyInspector(pulse_engine=self.pulse_engine_mock)

    def test_inspect_with_explicit_pulse_payload_and_negative_metrics(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        negative_val = -float(random.randint(1, 100))
        
        payload = {
            "metrics": {
                metric_name: negative_val
            }
        }

        result = self.inspector.inspect(self.repo_id, pulse_payload=payload)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], metric_name)
        self.assertEqual(result["anomalies"][0]["value"], negative_val)
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")
        self.assertAlmostEqual(result["deviation_score"], abs(negative_val))

    def test_inspect_with_threshold_exceeded(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        threshold_val = float(random.randint(10, 50))
        exceeded_val = threshold_val + float(random.randint(1, 50))

        payload = {
            "metrics": {
                metric_name: exceeded_val
            }
        }

        result = self.inspector.inspect(self.repo_id, pulse_payload=payload, threshold=threshold_val)

        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], metric_name)
        self.assertEqual(result["anomalies"][0]["value"], exceeded_val)
        self.assertEqual(result["anomalies"][0]["deviation"], "high")
        self.assertAlmostEqual(result["deviation_score"], exceeded_val - threshold_val)

    def test_inspect_fetches_pulse_via_get_pulse_when_payload_is_none(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=6))
        normal_val = float(random.randint(1, 5))
        
        self.pulse_engine_mock.get_pulse.return_value = {
            "metrics": {
                metric_name: normal_val
            }
        }
        
        # Убираем метод pulse, чтобы сработал get_pulse
        del self.pulse_engine_mock.pulse

        result = self.inspector.inspect(self.repo_id)

        self.pulse_engine_mock.get_pulse.assert_called_once_with(self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_fetches_pulse_via_pulse_method_fallback(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=6))
        normal_val = float(random.randint(1, 5))
        
        # Удаляем get_pulse, чтобы проверить фоллбек на метод pulse
        del self.pulse_engine_mock.get_pulse
        self.pulse_engine_mock.pulse.return_value = {
            "metrics": {
                metric_name: normal_val
            }
        }

        result = self.inspector.inspect(self.repo_id)

        self.pulse_engine_mock.pulse.assert_called_once_with(self.repo_id)
        self.assertFalse(result["is_anomaly"])

    def test_inspect_handles_none_payload_gracefully(self):
        self.pulse_engine_mock.get_pulse.return_value = None
        del self.pulse_engine_mock.pulse

        result = self.inspector.inspect(self.repo_id, pulse_payload=None)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_ignores_non_numeric_metric_values(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=7))
        invalid_val = ''.join(random.choices(string.ascii_uppercase, k=5))

        payload = {
            "metrics": {
                metric_name: invalid_val
            }
        }

        result = self.inspector.inspect(self.repo_id, pulse_payload=payload, threshold=1.0)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)


if __name__ == '__main__':
    unittest.main()