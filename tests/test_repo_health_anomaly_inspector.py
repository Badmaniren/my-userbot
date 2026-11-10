import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def setUp(self):
        self.mock_pulse_engine = MagicMock()
        self.inspector = RepoHealthAnomalyInspector(pulse_engine=self.mock_pulse_engine)

    def test_init_defaults(self):
        inspector = RepoHealthAnomalyInspector()
        self.assertIsNotNone(inspector.pulse_engine)
        self.assertIsNotNone(inspector.logger)

    def test_inspect_with_explicit_pulse_payload(self):
        r_id = uuid.uuid4().hex
        m_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        neg_val = -float(random.randint(1, 100))
        
        payload = {
            "repo_id": r_id,
            "metrics": {
                m_name: neg_val
            }
        }
        
        result = self.inspector.inspect(repo_id=r_id, pulse_payload=payload)
        
        self.assertEqual(result["repo_id"], r_id)
        self.assertEqual(result["status"], "inspected")
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], m_name)
        self.assertEqual(result["anomalies"][0]["value"], neg_val)
        self.assertEqual(result["anomalies"][0]["deviation"], "negative")
        self.assertEqual(result["deviation_score"], abs(neg_val))

    def test_inspect_fetches_via_get_pulse(self):
        r_id = uuid.uuid4().hex
        m_name = ''.join(random.choices(string.ascii_lowercase, k=6))
        high_val = float(random.randint(150, 300))
        threshold = float(random.randint(50, 100))
        
        self.mock_pulse_engine.get_pulse.return_value = {
            "metrics": {
                m_name: high_val
            }
        }
        
        if not hasattr(self.mock_pulse_engine, "get_pulse"):
            self.mock_pulse_engine.get_pulse = MagicMock()

        result = self.inspector.inspect(repo_id=r_id, threshold=threshold)
        
        self.mock_pulse_engine.get_pulse.assert_called_once_with(r_id)
        self.assertEqual(result["repo_id"], r_id)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["anomalies"][0]["deviation"], "high")
        self.assertEqual(result["deviation_score"], high_val - threshold)

    def test_inspect_fetches_via_pulse_fallback(self):
        r_id = uuid.uuid4().hex
        m_name = ''.join(random.choices(string.ascii_lowercase, k=7))
        val = float(random.randint(1, 50))
        
        del self.mock_pulse_engine.get_pulse
        self.mock_pulse_engine.pulse = MagicMock(return_value={
            "metrics": {
                m_name: val
            }
        })
        
        result = self.inspector.inspect(repo_id=r_id)
        
        self.mock_pulse_engine.pulse.assert_called_once_with(r_id)
        self.assertEqual(result["repo_id"], r_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_pulse_engine_no_methods(self):
        r_id = uuid.uuid4().hex
        engine_without_methods = object()
        inspector = RepoHealthAnomalyInspector(pulse_engine=engine_without_methods)
        
        result = inspector.inspect(repo_id=r_id)
        
        self.assertEqual(result["repo_id"], r_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])

    def test_inspect_malformed_payloads(self):
        r_id = uuid.uuid4().hex
        
        malformed_inputs = [None, "invalid_string_payload", 12345, []]
        
        for bad_payload in malformed_inputs:
            with self.subTest(bad_payload=bad_payload):
                result = self.inspector.inspect(repo_id=r_id, pulse_payload=bad_payload)
                self.assertEqual(result["repo_id"], r_id)
                self.assertFalse(result["is_anomaly"])
                self.assertEqual(result["anomalies"], [])

    def test_inspect_invalid_metrics_structure(self):
        r_id = uuid.uuid4().hex
        m_name = ''.join(random.choices(string.ascii_lowercase, k=5))
        
        payload = {
            "repo_id": r_id,
            "metrics": "not_a_dict"
        }
        
        result = self.inspector.inspect(repo_id=r_id, pulse_payload=payload)
        
        self.assertEqual(result["repo_id"], r_id)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["anomalies"], [])

    def test_inspect_mixed_metrics_and_types(self):
        r_id = uuid.uuid4().hex
        valid_metric = ''.join(random.choices(string.ascii_lowercase, k=6))
        bool_metric = ''.join(random.choices(string.ascii_lowercase, k=6))
        str_metric = ''.join(random.choices(string.ascii_lowercase, k=6))
        
        payload = {
            "repo_id": r_id,
            "metrics": {
                valid_metric: -10.0,
                bool_metric: True,
                str_metric: "ignored"
            }
        }
        
        result = self.inspector.inspect(repo_id=r_id, pulse_payload=payload)
        
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(len(result["anomalies"]), 1)
        self.assertEqual(result["anomalies"][0]["metric"], valid_metric)

    def test_repo_id_fallback_from_payload(self):
        r_id = uuid.uuid4().hex
        m_name = ''.join(random.choices(string.ascii_lowercase, k=6))
        
        payload = {
            "repo_id": r_id,
            "metrics": {
                m_name: -5.0
            }
        }
        
        result = self.inspector.inspect(repo_id=None, pulse_payload=payload)
        
        self.assertEqual(result["repo_id"], r_id)
        self.assertTrue(result["is_anomaly"])