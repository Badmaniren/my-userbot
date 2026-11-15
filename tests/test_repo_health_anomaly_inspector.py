import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.repo_path_mock = f"./repo_{uuid.uuid4().hex[:8]}"
        with patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            self.mock_logger_instance = MagicMock()
            mock_logger_cls.return_value = self.mock_logger_instance
            
            self.mock_pulse_engine = MagicMock()
            self.inspector = RepoHealthAnomalyInspector(pulse_engine=self.mock_pulse_engine)

    def test_init_defaults(self):
        with patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine") as mock_engine_cls, \
             patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            
            engine_instance = mock_engine_cls.return_value
            logger_instance = mock_logger_cls.return_value
            
            inspector = RepoHealthAnomalyInspector()
            self.assertEqual(inspector.pulse_engine, engine_instance)
            self.assertEqual(inspector.logger, logger_instance)

    def test_inspect_with_explicit_payload(self):
        repo_id = f"repo-{uuid.uuid4().hex[:6]}"
        metric_name_neg = f"metric_{uuid.uuid4().hex[:4]}"
        metric_name_high = f"metric_{uuid.uuid4().hex[:4]}"
        metric_name_normal = f"metric_{uuid.uuid4().hex[:4]}"
        
        neg_val = -float(random.randint(1, 100))
        high_val = float(random.randint(150, 300))
        normal_val = float(random.randint(0, 50))
        threshold = 100.0

        payload = {
            "repo_id": repo_id,
            "metrics": {
                metric_name_neg: neg_val,
                metric_name_high: high_val,
                metric_name_normal: normal_val,
                "bool_metric": True,
                "str_metric": f"invalid_{uuid.uuid4().hex[:4]}"
            }
        }

        result = self.inspector.inspect(repo_id=repo_id, pulse_payload=payload, threshold=threshold)

        self.assertEqual(result["repo_id"], repo_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 2)
        
        expected_deviation_score = abs(neg_val) + (high_val - threshold)
        self.assertAlmostEqual(result["deviation_score"], expected_deviation_score)
        
        self.mock_logger_instance.info.assert_called_once()

    def test_inspect_fetches_pulse_via_get_pulse(self):
        repo_id = f"repo-{uuid.uuid4().hex[:6]}"
        metric_name = f"metric_{uuid.uuid4().hex[:4]}"
        high_val = float(random.randint(500, 1000))
        threshold = 200.0

        self.mock_pulse_engine.get_pulse.return_value = {
            "repo_id": repo_id,
            "metrics": {metric_name: high_val}
        }
        
        del self.mock_pulse_engine.pulse

        result = self.inspector.inspect(repo_id=repo_id, threshold=threshold)

        self.mock_pulse_engine.get_pulse.assert_called_once_with(repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["anomalies"][0]["metric"], metric_name)
        self.assertEqual(result["anomalies"][0]["deviation"], "high")

    def test_inspect_fetches_pulse_via_pulse_method(self):
        repo_id = f"repo-{uuid.uuid4().hex[:6]}"
        metric_name = f"metric_{uuid.uuid4().hex[:4]}"
        neg_val = -float(random.randint(1, 50))

        del self.mock_pulse_engine.get_pulse
        self.mock_pulse_engine.pulse.return_value = {
            "repo_id": repo_id,
            "metrics": {metric_name: neg_val}
        }

        result = self.inspector.inspect(repo_id=repo_id)

        self.mock_pulse_engine.pulse.assert_called_once_with(repo_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")

    def test_inspect_fallback_when_no_engine_methods(self):
        repo_id = f"repo-{uuid.uuid4().hex[:6]}"
        
        del self.mock_pulse_engine.get_pulse
        del self.mock_pulse_engine.pulse

        result = self.inspector.inspect(repo_id=repo_id)

        self.assertEqual(result["repo_id"], repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_invalid_payload_type_falls_back(self):
        invalid_payloads = [
            f"not_a_dict_{uuid.uuid4().hex[:4]}",
            random.randint(1, 100),
            None
        ]

        for invalid_payload in invalid_payloads:
            self.mock_pulse_engine.get_pulse.return_value = {}
            repo_id = f"repo-{uuid.uuid4().hex[:6]}"
            
            result = self.inspector.inspect(repo_id=repo_id, pulse_payload=invalid_payload)
            self.assertEqual(result["repo_id"], repo_id)
            self.assertFalse(result["is_anomaly"])

    def test_inspect_metrics_not_a_dict(self):
        repo_id = f"repo-{uuid.uuid4().hex[:6]}"
        payload = {
            "repo_id": repo_id,
            "metrics": f"invalid_metrics_{uuid.uuid4().hex[:4]}"
        }

        result = self.inspector.inspect(repo_id=repo_id, pulse_payload=payload)

        self.assertEqual(result["repo_id"], repo_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])

    def test_inspect_no_anomalies_found(self):
        repo_id = f"repo-{uuid.uuid4().hex[:6]}"
        metric_name = f"metric_{uuid.uuid4().hex[:4]}"
        normal_val = float(random.randint(1, 50))
        threshold = 100.0

        payload = {
            "repo_id": repo_id,
            "metrics": {metric_name: normal_val}
        }

        result = self.inspector.inspect(repo_id=repo_id, pulse_payload=payload, threshold=threshold)

        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])
        self.assertEqual(result["deviation_score"], 0.0)
        self.mock_logger_instance.info.assert_called_once()