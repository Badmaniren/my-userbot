import unittest
import uuid
import random
from skills.incident_sla_breach_analyzer import IncidentSLABreachAnalyzer, incident_sla_breach_analyzer
from skills.incident_sla_tracker import incident_sla_tracker


class TestIncidentSLABreachAnalyzerIntegration(unittest.TestCase):
    def test_integration_breach_analyzer_flow(self):
        rand_id = str(uuid.uuid4())
        metric_name = f"metric_{random.randint(100, 999)}"
        metric_value = round(random.uniform(5.0, 50.0), 2)

        incident_data = {
            "id": rand_id,
            "metric": metric_name,
            "duration": round(random.uniform(1.0, 10.0), 2)
        }

        tracking_metrics = {
            metric_name: metric_value
        }

        analyzer = IncidentSLABreachAnalyzer()

        # Real call to dependent module without mocks
        tracker_state = incident_sla_tracker.fetch_current_state()
        self.assertIsInstance(tracker_state, (dict, list, type(None)))

        historical_data = [incident_data]
        risk_result = analyzer.analyze_breach_risk(historical_data, tracking_metrics)

        self.assertIn(rand_id, risk_result)
        self.assertEqual(risk_result[rand_id]["breach_risk_score"], float(metric_value))
        self.assertTrue(risk_result[rand_id]["is_breach_imminent"])

        wrapper_result = incident_sla_breach_analyzer(rand_id, incident_data, metric_value)

        self.assertIsInstance(wrapper_result, dict)
        self.assertEqual(wrapper_result.get("incident_id"), rand_id)
        self.assertEqual(wrapper_result.get("breach_risk"), float(metric_value))


if __name__ == "__main__":
    unittest.main()