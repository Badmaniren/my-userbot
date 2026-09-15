import unittest
import uuid
import random
from datetime import datetime
from skills.incident_aggregator import IncidentAggregator
from skills.error_recovery_hub import ErrorRecoveryHub

class TestIncidentAggregatorIntegration(unittest.TestCase):
    def test_build_analytics_real_integration(self):
        hub = ErrorRecoveryHub()
        aggregator = IncidentAggregator(hub=hub)

        module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        random_error_msg = f"Error_{uuid.uuid4().hex[:6]}"
        random_tb = f"Traceback at line {random.randint(1, 100)}"

        try:
            raise RuntimeError(random_error_msg)
        except RuntimeError as e:
            hub.capture_failure(module_name, e, random_tb)

        analytics = aggregator.build_analytics(module_name)

        self.assertIsInstance(analytics, dict)
        self.assertEqual(analytics.get("module"), module_name)
        self.assertGreaterEqual(analytics.get("total_incidents"), 1)
        self.assertIn("success_rate", analytics)

        history = hub.get_incident_history(module_name)
        self.assertTrue(any(h.get("error") == random_error_msg for h in history))

if __name__ == "__main__":
    unittest.main()