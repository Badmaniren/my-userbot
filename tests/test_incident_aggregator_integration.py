import unittest
import uuid
import random
from skills.incident_aggregator import IncidentAggregator, aggregate_incidents


class TestIncidentAggregatorIntegration(unittest.TestCase):

    def test_process_and_aggregate_integration(self):
        aggregator = IncidentAggregator()
        
        random_module = f"test_module_{uuid.uuid4().hex[:8]}"
        random_error_msg = f"Simulated security exception {random.randint(1000, 9999)}"
        exception_instance = RuntimeError(random_error_msg)
        traceback_str = f"Traceback (most recent call last):\n  File '{random_module}.py', line {random.randint(1, 100)}, in <module>\n    raise RuntimeError('{random_error_msg}')"

        result = aggregator.process_and_aggregate(
            module_name=random_module,
            exception=exception_instance,
            traceback_str=traceback_str
        )

        self.assertIsInstance(result, dict)
        self.assertIn("incident_id", result)
        self.assertIsNotNone(result["incident_id"])
        
        self.assertEqual(result["module_name"], random_module)
        self.assertIn("analysis", result)
        self.assertIn("metrics", result)
        self.assertIn("metrics_summary", result)
        self.assertIn("history", result)

        self.assertIsInstance(result["metrics_summary"], dict)
        self.assertIsInstance(result["history"], list)

    def test_aggregate_incidents_function(self):
        random_module = f"stream_module_{uuid.uuid4().hex[:8]}"
        random_error_msg = f"Critical alert {random.randint(500, 999)}"
        exception_instance = ValueError(random_error_msg)
        traceback_str = f"Traceback:\nValueError: {random_error_msg}"

        result = aggregate_incidents(
            module_name=random_module,
            exception=exception_instance,
            traceback_str=traceback_str
        )

        self.assertIsInstance(result, dict)
        self.assertIn("incident_id", result)
        self.assertIsNotNone(result["incident_id"])
        self.assertEqual(result["module_name"], random_module)
        self.assertIn("metrics_summary", result)


if __name__ == "__main__":
    unittest.main()