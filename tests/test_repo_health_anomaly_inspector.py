import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.rand_repo_id = uuid.uuid4().hex
        self.rand_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.pulse_engine_mock = MagicMock()
        self.logger_mock = MagicMock()

    def test_init_default_dependencies(self):
        with patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine") as mock_pulse_cls, \
             patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            
            inspector = RepoHealthAnomalyInspector()
            mock_pulse_cls.assert_called_once()
            mock_logger_cls.assert_called_once_with(repo_path=".")
            self.assertIsNotNone(inspector.pulse_engine)
            self.assertIsNotNone(inspector.logger)

    def test_inspect_with_explicit_payload_no_anomalies(self):
        rand_val = round(random.uniform(0.0, 50.0), 2)
        payload = {
            "repo_id": self.rand_repo_id,
            "metrics": {
                self.rand_metric_name: rand_val
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=self.pulse_engine_mock)
        inspector.logger = self.logger_mock

        result = inspector.inspect(repo_id=self.rand_repo_id, pulse_payload=payload)

        self.assertEqual(result["repo_id"], self.rand_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 0)
        self.assertEqual(result["deviation_score"], 0.0)
        self.logger_mock.info.assert_called_once()

    def test_inspect_negative_metric_anomaly(self):
        rand_neg_val = -round(random.uniform(1.0, 100.0), 2)
        payload = {
            "repo_id": self.rand_repo_id,
            "metrics": {
                self.rand_metric_name: rand_neg_val
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=self.pulse_engine_mock)
        inspector.logger = self.logger_mock

        result = inspector.inspect(repo_id=self.rand_repo_id, pulse_payload=payload)

        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.rand_metric_name)
        self.assertEqual(result["anomalies"][0]["value"], rand_neg_val)
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")
        self.assertEqual(result["deviation_score"], abs(rand_neg_val))

    def test_inspect_high_threshold_anomaly(self):
        rand_high_val = round(random.uniform(150.0, 300.0), 2)
        rand_threshold = round(random.uniform(50.0, 100.0), 2)
        payload = {
            "repo_id": self.rand_repo_id,
            "metrics": {
                self.rand_metric_name: rand_high_val
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=self.pulse_engine_mock)
        inspector.logger = self.logger_mock

        result = inspector.inspect(repo_id=self.rand_repo_id, pulse_payload=payload, threshold=rand_threshold)

        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], self.rand_metric_name)
        self.assertEqual(result["anomalies"][0]["value"], rand_high_val)
        self.assertEqual(result["anomalies"][0]["deviation"], "high")
        expected_score = rand_high_val - rand_threshold
        self.assertAlmostEqual(result["deviation_score"], expected_score)

    def test_inspect_fetches_pulse_via_get_pulse(self):
        rand_val = round(random.uniform(10.0, 50.0), 2)
        self.pulse_engine_mock.get_pulse.return_value = {
            "repo_id": self.rand_repo_id,
            "metrics": {
                self.rand_metric_name: rand_val
            }
        }
        # Удаляем метод pulse, чтобы сработал get_pulse
        if hasattr(self.pulse_engine_mock, "pulse"):
            del self.pulse_engine_mock.pulse

        inspector = RepoHealthAnomalyInspector(pulse_engine=self.pulse_engine_mock)
        inspector.logger = self.logger_mock

        result = inspector.inspect(repo_id=self.rand_repo_id)

        self.pulse_engine_mock.get_pulse.assert_called_once_with(self.rand_repo_id)
        self.assertEqual(result["repo_id"], self.rand_repo_id)
        self.assertFalse(result["is_anomaly"])

    def test_inspect_fetches_pulse_via_pulse_fallback(self):
        rand_val = round(random.uniform(10.0, 50.0), 2)
        # Удаляем get_pulse
        if hasattr(self.pulse_engine_mock, "get_pulse"):
            del self.pulse_engine_mock.get_pulse
        
        self.pulse_engine_mock.pulse.return_value = {
            "repo_id": self.rand_repo_id,
            "metrics": {
                self.rand_metric_name: rand_val
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=self.pulse_engine_mock)
        inspector.logger = self.logger_mock

        result = inspector.inspect(repo_id=self.rand_repo_id)

        self.pulse_engine_mock.pulse.assert_called_once_with(self.rand_repo_id)
        self.assertEqual(result["repo_id"], self.rand_repo_id)

    def test_inspect_invalid_payload_types_handled_gracefully(self):
        inspector = RepoHealthAnomalyInspector(pulse_engine=self.pulse_engine_mock)
        inspector.logger = self.logger_mock

        rand_invalid_payload = ''.join(random.choices(string.ascii_letters, k=15))
        result = inspector.inspect(repo_id=self.rand_repo_id, pulse_payload=rand_invalid_payload)

        self.assertEqual(result["repo_id"], self.rand_repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_ignores_non_numeric_metrics(self):
        rand_str_val = uuid.uuid4().hex
        payload = {
            "repo_id": self.rand_repo_id,
            "metrics": {
                self.rand_metric_name: rand_str_val,
                "boolean_metric": True,
                "none_metric": None
            }
        }

        inspector = RepoHealthAnomalyInspector(pulse_engine=self.pulse_engine_mock)
        inspector.logger = self.logger_mock

        result = inspector.inspect(repo_id=self.rand_repo_id, pulse_payload=payload)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)


if __name__ == "__main__":
    unittest.main()