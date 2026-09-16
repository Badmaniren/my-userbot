import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_end_to_end_sla_workflow(self):
        rand_suffix = str(uuid.uuid4())[:8]
        incident_id = f"INC-{rand_suffix}"
        severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        
        thresholds = {"LOW": 7200, "MEDIUM": 3600, "HIGH": 1800, "CRITICAL": 600}
        warning_pct = 0.8
        
        tracker = IncidentSLATracker(sla_thresholds=thresholds, warning_threshold_pct=warning_pct)
        
        created_time = datetime.now() - timedelta(seconds=random.randint(100, 5000))
        tracker.register_incident(incident_id=incident_id, severity=severity_level, created_at=created_time)
        
        time_to_breach = tracker.get_time_to_breach(incident_id)
        self.assertIsInstance(time_to_breach, float)

        breaches = tracker.check_sla_breaches(current_time=datetime.now())
        self.assertIsInstance(breaches, list)

        agg_input = {
            "incident_id": incident_id,
            "severity": severity_level,
            "data": {"timestamp": int(created_time.timestamp())}
        }
        aggregated = aggregate_incidents([agg_input])
        self.assertIsInstance(aggregated, (dict, list))
        
        sla_input = {
            "incident_id": incident_id,
            "aggregated_data": {"data": {"timestamp": int(created_time.timestamp())}},
            "threshold_seconds": thresholds[severity_level]
        }

        result = track_incident_sla(sla_input)
        self.assertIn("incident_id", result)
        self.assertEqual(result["incident_id"], incident_id)
        self.assertIn("breach_predicted", result)
        self.assertIn("time_remaining_seconds", result)

        tracker.update_incident_status(incident_id, "RESOLVED")
        resolved_breaches = tracker.check_sla_breaches()
        self.not_found_active = not any(b["incident_id"] == incident_id for b in resolved_breaches)
        self.assertTrue(self.not_found_active)

if __name__ == "__main__":
    unittest.main()