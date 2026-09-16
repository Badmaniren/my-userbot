import unittest
import uuid
import random
import io
from skills.incident_sla_breach_analyzer import IncidentSLABreachAnalyzer, incident_sla_breach_analyzer

class TestIncidentSLABreachAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = IncidentSLABreachAnalyzer()
        self.random_id = str(uuid.uuid4())
        self.metric_name = f"metric_{uuid.uuid4().hex[:6]}"

    def test_analyze_breach_risk_normal(self):
        duration = float(random.randint(5, 50))
        current_val = float(random.randint(1, 100))
        historical_data = [{
            "id": self.random_id,
            "metric": self.metric_name,
            "duration": duration
        }]
        tracking_metrics = {
            self.metric_name: current_val
        }
        result = self.analyzer.analyze_breach_risk(historical_data, tracking_metrics)
        self.assertIn(self.random_id, result)
        self.assertEqual(result[self.random_id]["breach_risk_score"], float(current_val))
        self.assertEqual(result[self.random_id]["is_breach_imminent"], current_val > duration)

    def test_analyze_breach_risk_empty_metrics(self):
        historical_data = [{
            "id": self.random_id,
            "metric": self.metric_name,
            "duration": float(random.randint(10, 20))
        }]
        result = self.analyzer.analyze_breach_risk(historical_data, {})
        self.assertIn(self.random_id, result)
        self.assertEqual(result[self.random_id]["breach_risk_score"], 0.0)
        self.assertFalse(result[self.random_id]["is_breach_imminent"])

    def test_parse_and_analyze_stream(self):
        val = round(random.uniform(1.0, 100.0), 2)
        stream_content = f"timestamp:123456,value:{val},status:active".encode("utf-8")

        class DummyFile:
            def __enter__(self):
                return io.BytesIO(stream_content)
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        import unittest.mock
        with unittest.mock.patch("builtins.open", return_value=DummyFile()):
            res = self.analyzer.parse_and_analyze_stream(f"path_{uuid.uuid4().hex}.csv")
            self.assertEqual(res["parsed_value"], val)

    def test_wrapper_function(self):
        tracking_val = float(random.randint(1, 50))
        incident_data = {
            "id": self.random_id,
            "metric": self.metric_name
        }
        res = incident_sla_breach_analyzer(self.random_id, incident_data, tracking_val)
        self.assertEqual(res["incident_id"], self.random_id)
        self.assertIsInstance(res["breach_risk"], float)

if __name__ == "__main__":
    unittest.main()