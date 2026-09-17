import unittest
import uuid
import random
from skills.incident_sla_health_sync import sync_sla_to_health_aggregator
from skills.incident_sla_tracker import IncidentSLATracker
from skills.system_health_aggregator import SystemHealthAggregator


class TestIncidentSlaHealthSyncIntegration(unittest.TestCase):

    def test_sync_sla_to_health_aggregator_integration(self):
        random_incident_id = f"inc-{uuid.uuid4()}"
        statuses = ["BREACHED", "WARNING", "HEALTHY", "CRITICAL"]
        random_sla_status = random.choice(statuses)
        random_impact_score = round(random.uniform(0.0, 100.0), 2)

        test_payload = {
            "incident_id": random_incident_id,
            "sla_status": random_sla_status,
            "impact_score": random_impact_score
        }

        result = sync_sla_to_health_aggregator(test_payload)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("incident_id"), random_incident_id)

        tracker = IncidentSLATracker()
        tracked_data = tracker.get_incident_data(random_incident_id)
        self.assertIsNotNone(tracked_data)
        self.assertEqual(tracked_data.get("status"), random_sla_status)

        aggregator = SystemHealthAggregator()
        health_data = aggregator.get_system_health(random_incident_id)
        self.assertIsNotNone(health_data)
        self.assertEqual(health_data.get("impact_score"), random_impact_score)


if __name__ == "__main__":
    unittest.main()