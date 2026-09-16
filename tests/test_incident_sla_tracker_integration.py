import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity
from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla


class RealIncidentBridge:
    def __init__(self):
        self.notified = []
        self.escalated = []

    def notify_sla_breach(self, incident_id: str, severity: str):
        self.notified.append({"incident_id": incident_id, "severity": severity})

    def escalate_incident(self, incident_id: str, severity: str):
        self.escalated.append({"incident_id": incident_id, "severity": severity})


class TestIncidentSLATrackerIntegration(unittest.TestCase):

    def test_end_to_end_sla_lifecycle(self):
        rand_suffix = str(uuid.uuid4())[:8]
        incident_id = f"INC-{rand_suffix}"

        severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        chosen_severity = random.choice(severities)
        
        evaluated_sev = evaluate_incident_severity({
            "incident_id": incident_id,
            "raw_severity": chosen_severity
        })

        aggregated = aggregate_incidents({
            "incident_id": incident_id,
            "severity": evaluated_sev.get("severity", chosen_severity)
        })

        thresholds = {
            "LOW": 7200,
            "MEDIUM": 3600,
            "HIGH": 1800,
            "CRITICAL": 600
        }
        
        tracker = IncidentSLATracker(
            sla_thresholds=thresholds,
            warning_threshold_pct=0.8
        )
        
        past_seconds = random.randint(300, 5000)
        created_at = datetime.now() - timedelta(seconds=past_seconds)
        
        tracker.register_incident(
            incident_id=incident_id,
            severity=evaluated_sev.get("severity", chosen_severity),
            created_at=created_at
        )
        
        time_to_breach = tracker.get_time_to_breach(incident_id=incident_id)
        self.assertIsInstance(time_to_breach, float)

        bridge = RealIncidentBridge()

        breach_results = tracker.check_sla_breaches(
            notification_bridge=bridge,
            escalation_engine=bridge
        )

        self.assertIsInstance(breach_results, list)

        found_incident = None
        for res in breach_results:
            if res["incident_id"] == incident_id:
                found_incident = res
                break

        if past_seconds > thresholds.get(evaluated_sev.get("severity", chosen_severity), 3600):
            self.assertIsNotNone(found_incident)
            self.assertEqual(found_incident["status"], "BREACHED")
            self.assertTrue(any(n["incident_id"] == incident_id for n in bridge.notified))
            self.assertTrue(any(e["incident_id"] == incident_id for e in bridge.escalated))

        random_threshold = random.randint(1000, 10000)
        sla_input = {
            "incident_id": incident_id,
            "aggregated_data": aggregated,
            "threshold_seconds": random_threshold
        }
        
        tracker_result = track_incident_sla(sla_input)
        self.assertIsInstance(tracker_result, dict)
        self.assertEqual(tracker_result["incident_id"], incident_id)
        self.assertIn("breach_predicted", tracker_result)
        self.assertIn("time_remaining_seconds", tracker_result)


if __name__ == "__main__":
    unittest.main()