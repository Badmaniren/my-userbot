import unittest
from unittest.mock import MagicMock, patch
import random
import uuid
import string
from skills.repo_health_anomaly_inspector import RepoHealthAnomalyInspector


class TestRepoHealthAnomalyInspector(unittest.TestCase):

    def test_init_defaults(self):
        with patch("skills.repo_health_anomaly_inspector.RepoHealthPulseEngine") as mock_engine_cls, \
             patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            inspector = RepoHealthAnomalyInspector()
            mock_engine_cls.assert_called_once()
            mock_logger_cls.assert_called_once_with(repo_path=".")
            self.assertIsNotNone(inspector.pulse_engine)
            self.assertIsNotNone(inspector.logger)

    def test_init_custom_engine(self):
        custom_engine = MagicMock()
        with patch("skills.repo_health_anomaly_inspector.RepoLogger") as mock_logger_cls:
            inspector = RepoHealthAnomalyInspector(pulse_engine=custom_engine)
            self.assertEqual(inspector.pulse_engine, custom_engine)
            mock_logger_cls.assert_called_once_with(repo_path=".")

    def test_inspect_negative_metrics_detection(self):
        custom_engine = MagicMock()
        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=custom_engine)
            
            repo_id = f"repo-{uuid.uuid4().hex}"
            metric_name = f"metric_{uuid.uuid4().hex}"
            negative_val = -round(random.uniform(1.0, 100.0), 3)

            payload = {
                "repo_id": repo_id,
                "metrics": {
                    metric_name: negative_val
                }
            }

            result = inspector.inspect(repo_id=repo_id, pulse_payload=payload)

            self.assertEqual(result["repo_id"], repo_id)
            self.assertEqual(result["status"], "inspected")
            self.assertTrue(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 1)
            self.assertEqual(result["anomalies"][0]["metric"], metric_name)
            self.assertEqual(result["anomalies"][0]["value"], negative_val)
            self.assertEqual(result["anomalies"][0]["deviation"], "negative")
            self.assertAlmostEqual(result["deviation_score"], abs(negative_val), places=4)

    def test_inspect_high_threshold_metrics_detection(self):
        custom_engine = MagicMock()
        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=custom_engine)

            repo_id = f"repo-{uuid.uuid4().hex}"
            metric_name = f"metric_{uuid.uuid4().hex}"
            threshold = round(random.uniform(10.0, 50.0), 2)
            high_val = threshold + round(random.uniform(1.0, 25.0), 2)

            payload = {
                "repo_id": repo_id,
                "metrics": {
                    metric_name: high_val
                }
            }

            result = inspector.inspect(repo_id=repo_id, pulse_payload=payload, threshold=threshold)

            self.assertTrue(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 1)
            self.assertEqual(result["anomalies"][0]["metric"], metric_name)
            self.assertEqual(result["anomalies"][0]["value"], high_val)
            self.assertEqual(result["anomalies"][0]["deviation"], "high")
            self.assertAlmostEqual(result["deviation_score"], high_val - threshold, places=4)

    def test_inspect_below_threshold_normal_metrics(self):
        custom_engine = MagicMock()
        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=custom_engine)

            repo_id = f"repo-{uuid.uuid4().hex}"
            metric_name = f"metric_{uuid.uuid4().hex}"
            threshold = round(random.uniform(50.0, 100.0), 2)
            normal_val = threshold - round(random.uniform(1.0, 10.0), 2)

            payload = {
                "repo_id": repo_id,
                "metrics": {
                    metric_name: normal_val
                }
            }

            result = inspector.inspect(repo_id=repo_id, pulse_payload=payload, threshold=threshold)

            self.assertFalse(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 0)
            self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_ignores_boolean_and_non_numeric_metrics(self):
        custom_engine = MagicMock()
        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=custom_engine)

            repo_id = f"repo-{uuid.uuid4().hex}"
            payload = {
                "repo_id": repo_id,
                "metrics": {
                    f"bool_true_{uuid.uuid4().hex}": True,
                    f"bool_false_{uuid.uuid4().hex}": False,
                    f"str_{uuid.uuid4().hex}": uuid.uuid4().hex,
                    f"none_{uuid.uuid4().hex}": None,
                    f"list_{uuid.uuid4().hex}": [random.randint(1, 10)]
                }
            }

            result = inspector.inspect(repo_id=repo_id, pulse_payload=payload, threshold=1.0)
            self.assertFalse(result["is_anomaly"])
            self.assertEqual(len(result["anomalies"]), 0)
            self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_fetches_payload_from_engine_get_pulse(self):
        engine = MagicMock()
        rand_repo_id = f"repo-{uuid.uuid4().hex}"
        rand_metric = f"metric_{uuid.uuid4().hex}"
        rand_val = -round(random.uniform(1.0, 10.0), 2)

        engine.get_pulse.return_value = {
            "repo_id": rand_repo_id,
            "metrics": {rand_metric: rand_val}
        }

        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=engine)
            result = inspector.inspect(repo_id=rand_repo_id)

            engine.get_pulse.assert_called_once_with(rand_repo_id)
            self.assertTrue(result["is_anomaly"])
            self.assertEqual(result["anomalies"][0]["metric"], rand_metric)

    def test_inspect_fetches_payload_from_engine_pulse_fallback(self):
        class PulseOnlyEngine:
            def pulse(self, repo_id):
                return {"repo_id": repo_id, "metrics": {}}

        engine = PulseOnlyEngine()
        rand_repo_id = f"repo-{uuid.uuid4().hex}"

        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=engine)
            result = inspector.inspect(repo_id=rand_repo_id)
            self.assertEqual(result["repo_id"], rand_repo_id)
            self.assertFalse(result["is_anomaly"])

    def test_inspect_engine_without_supported_methods(self):
        class EmptyEngine:
            pass

        engine = EmptyEngine()
        rand_repo_id = f"repo-{uuid.uuid4().hex}"

        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=engine)
            result = inspector.inspect(repo_id=rand_repo_id)
            self.assertEqual(result["repo_id"], rand_repo_id)
            self.assertFalse(result["is_anomaly"])

    def test_inspect_invalid_payload_types(self):
        custom_engine = MagicMock()
        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=custom_engine)

            for invalid_payload in [uuid.uuid4().hex, [random.randint(1, 10)], random.randint(100, 500)]:
                result = inspector.inspect(pulse_payload=invalid_payload)
                self.assertEqual(result["repo_id"], "default-repo")
                self.assertFalse(result["is_anomaly"])
                self.assertEqual(result["deviation_score"], 0.0)

    def test_inspect_repo_id_fallback_chain(self):
        custom_engine = MagicMock()
        with patch("skills.repo_health_anomaly_inspector.RepoLogger"):
            inspector = RepoHealthAnomalyInspector(pulse_engine=custom_engine)

            payload_repo_id = f"payload-repo-{uuid.uuid4().hex}"
            payload = {"repo_id": payload_repo_id, "metrics": {}}

            result = inspector.inspect(repo_id=None, pulse_payload=payload)
            self.assertEqual(result["repo_id"], payload_repo_id)

            empty_payload = {}
            result_default = inspector.inspect(repo_id=None, pulse_payload=empty_payload)
            self.assertEqual(result_default["repo_id"], "default-repo")

    def test_inspect_logger_invoked_correctly(self):
        mock_logger = MagicMock()
        custom_engine = MagicMock()
        with patch("skills.repo_health_anomaly_inspector.RepoLogger", return_value=mock_logger):
            inspector = RepoHealthAnomalyInspector(pulse_engine=custom_engine)
            rand_repo_id = f"repo-{uuid.uuid4().hex}"
            metric_name = f"metric_{uuid.uuid4().hex}"
            negative_val = -round(random.uniform(5.0, 15.0), 2)
            payload = {"metrics": {metric_name: negative_val}}

            inspector.inspect(repo_id=rand_repo_id, pulse_payload=payload)
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            self.assertIn(rand_repo_id, log_message)
            self.assertIn("is_anomaly: True", log_message)
            self.assertIn("anomalies_count: 1", log_message)


if __name__ == "__main__":
    unittest.main()