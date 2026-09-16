import unittest
import uuid
import random
import time

from skills.incident_aggregator import IncidentAggregator
from skills.incident_impact_analyzer import IncidentImpactAnalyzer
from skills.incident_sla_sla_tracker import IncidentSlaTracker, SlaState

class TestIncidentSlaTrackerIntegration(unittest.TestCase):
    def test_sla_tracker_lifecycle_integration(self):
        incident_id = f"inc-{uuid.uuid4()}"

        tracker = IncidentSlaTracker(
            incident_aggregator=IncidentAggregator(),
            impact_analyzer=IncidentImpactAnalyzer()
        )

        init_result = tracker.initialize_incident_sla(incident_id)

        self.assertIsInstance(init_result, dict)
        self.assertEqual(init_result["incident_id"], incident_id)
        self.assertEqual(init_result["state"], SlaState.TRACKING.value)
        self.assertIn("limit_seconds", init_result)
        self.assertIn("start_time", init_result)

        is_violated = tracker.check_violation(incident_id)
        self.assertIsInstance(is_violated, bool)

        resolution_code = f"RES-{random.randint(1000, 9999)}"
        resolve_result = tracker.resolve_incident(incident_id, resolution_code)

        self.assertIsInstance(resolve_result, dict)
        self.assertTrue(resolve_result["success"])
        self.assertEqual(resolve_result["resolution_code"], resolution_code)

        report = tracker.generate_sla_report()
        self.assertIsInstance(report, dict)

if __name__ == "__main__":
    unittest.main()