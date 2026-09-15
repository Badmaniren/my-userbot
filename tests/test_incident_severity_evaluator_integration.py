import unittest
import uuid
import random
import os
from skills.incident_severity_evaluator import evaluate_incident_severity

class TestIncidentSeverityEvaluatorIntegration(unittest.TestCase):
    def test_evaluate_incident_severity_composition(self):
        module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        exception_name = "RuntimeError"
        traceback_str = f"Traceback (most recent call last):\n  File \"{module_name}.py\", line {random.randint(1, 100)}, in <module>\n    raise {exception_name}(\"Critical failure {uuid.uuid4()}\")"
        incident_id = f"INC-{random.randint(1000, 9999)}"

        result = evaluate_incident_severity(
            module_name=module_name,
            exception=exception_name,
            traceback_str=traceback_str,
            incident_id=incident_id
        )

        self.assertIsInstance(result, dict)
        self.assertIn("incident_id", result)
        self.assertEqual(result["incident_id"], incident_id)
        self.assertIn("severity_score", result)
        self.assertIn("trend_metrics", result)
        self.assertIn("aggregated_data", result)

if __name__ == "__main__":
    unittest.main()