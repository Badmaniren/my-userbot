import unittest
import os
import uuid
import random
import tempfile
from skills.incident_auto_escalation_engine import IncidentAutoEscalationEngine
from skills.incident_aggregator import IncidentAggregator
from skills.incident_severity_evaluator import IncidentSeverityEvaluator
from skills.incident_trend_analyzer import IncidentTrendAnalyzer

class TestIncidentAutoEscalationEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.aggregator = IncidentAggregator()
        self.evaluator = IncidentSeverityEvaluator()
        self.analyzer = IncidentTrendAnalyzer()
        self.engine = IncidentAutoEscalationEngine(
            incident_aggregator=self.aggregator,
            severity_evaluator=self.evaluator,
            trend_analyzer=self.analyzer
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_process_escalation_integration(self):
        random_id = f"inc-{uuid.uuid4()}"
        rand_severity = random.randint(1, 100)
        rand_history = random.randint(0, 10)

        self.aggregator.incidents[random_id] = {
            "severity_score": rand_severity,
            "failure_history_count": rand_history,
            "metric_value": float(rand_severity),
            "storage_path": self.temp_dir.name
        }

        result = self.engine.process_escalation(random_id)

        self.assertEqual(result["incident_id"], random_id)
        self.assertIn("escalation_tier", result)
        self.assertIn("severity_score", result)

        updated_details = self.aggregator.get_incident_details(random_id)
        self.assertEqual(updated_details.get("status"), "escalated")
        self.assertEqual(updated_details.get("tier"), result["escalation_tier"])

    def test_evaluate_and_escalate_creates_lock_file(self):
        random_id = f"inc-{uuid.uuid4()}"
        rand_metric = random.uniform(1.0, 500.0)

        self.aggregator.incidents[random_id] = {
            "metric_value": rand_metric,
            "storage_path": self.temp_dir.name
        }

        result = self.engine.evaluate_and_escalate(random_id)

        self.assertTrue(result["escalated"])
        self.assertEqual(result["target_incident_id"], random_id)

        expected_lock_file = os.path.join(self.temp_dir.name, f"escalation_{random_id}.lock")
        self.assertTrue(os.path.exists(expected_lock_file))

        with open(expected_lock_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(str(rand_metric), content)

if __name__ == "__main__":
    unittest.main()