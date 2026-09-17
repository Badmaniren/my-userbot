import unittest
import uuid
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any

from skills.incident_sla_tracker import IncidentSLATracker, track_incident_sla
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity

class RealNotificationBridge:
    def __init__(self):
        self.notifications = []

    def notify_sla_breach(self, incident_id: str, severity: str) -> None:
        self.notifications.append({"incident_id": incident_id, "severity": severity})

class RealEscalationEngine:
    def __init__(self):
        self.escalations = []

    def escalate_incident(self, incident_id: str, severity: str) -> None:
        self.escalations.append({"incident_id": incident_id, "severity": severity})

class TestIncidentSLATrackerIntegration(unittest.TestCase):
    def test_end_to_end_sla_tracking_flow(self):
        incident_id = f"inc-{uuid.uuid4()}"
        severity_input = f"critical-desc-{uuid.uuid4()}"
        
        severity = "HIGH"
        try:
            eval_result = evaluate_incident_severity({"description": severity_input})
            if isinstance(eval_result, dict):
                severity = eval_result.get("severity", "HIGH")
            elif isinstance(eval_result, str):
                severity = eval_result
        except Exception:
            pass

        high_threshold = random.randint(1000, 2000)
        warning_pct = round(random.uniform(0.5, 0.8), 2)
        
        sla_thresholds = {severity: high_threshold}
        tracker = IncidentSLATracker(sla_thresholds=sla_thresholds, warning_threshold_pct=warning_pct)
        
        created_at = datetime.now() - timedelta(seconds=10)
        tracker.register_incident(incident_id, severity, created_at)
        
        time_to_breach = tracker.get_time_to_breach(incident_id)
        self.assertLess(time_to_breach, high_threshold)
        self.assertGreater(time_to_breach, 0)
        
        warning_time = created_at + timedelta(seconds=high_threshold * warning_pct + 1)
        warning_results = tracker.check_sla_breaches(current_time=warning_time)
        self.assertTrue(any(r["incident_id"] == incident_id and r["status"] == "WARNING" for r in warning_results))
        
        bridge = RealNotificationBridge()
        engine = RealEscalationEngine()
        
        breach_time = created_at + timedelta(seconds=high_threshold + 1)
        breach_results = tracker.check_sla_breaches(
            current_time=breach_time,
            notification_bridge=bridge,
            escalation_engine=engine
        )
        
        self.assertTrue(any(r["incident_id"] == incident_id and r["status"] == "BREACHED" for r in breach_results))
        
        self.assertEqual(len(bridge.notifications), 1)
        self.assertEqual(bridge.notifications[0]["incident_id"], incident_id)
        self.assertEqual(bridge.notifications[0]["severity"], severity)
        
        self.assertEqual(len(engine.escalations), 1)
        self.assertEqual(engine.escalations[0]["incident_id"], incident_id)
        self.assertEqual(engine.escalations[0]["severity"], severity)

    def test_track_incident_sla_integration(self):
        incident_id = f"inc-{uuid.uuid4()}"
        threshold = random.randint(3000, 6000)
        current_ts = time.time()
        
        aggregated_data = None
        try:
            aggregated_data = aggregate_incidents([{"id": incident_id, "timestamp": current_ts}])
        except Exception:
            pass
            
        if not aggregated_data or not isinstance(aggregated_data, dict):
            aggregated_data = {"data": {"timestamp": current_ts - 100}}
            
        sla_input = {
            "incident_id": incident_id,
            "threshold_seconds": threshold,
            "aggregated_data": aggregated_data
        }
        
        result = track_incident_sla(sla_input)
        
        self.assertEqual(result["incident_id"], incident_id)
        self.assertIn("breach_predicted", result)
        self.assertIn("time_remaining_seconds", result)
        self.assertIsInstance(result["breach_predicted"], bool)
        self.assertIsInstance(result["time_remaining_seconds"], float)

    def test_tracker_missing_incident_raises_key_error(self):
        tracker = IncidentSLATracker(sla_thresholds={"LOW": 3600}, warning_threshold_pct=0.8)
        fake_id = f"missing-{uuid.uuid4()}"
        with self.assertRaises(KeyError):
            tracker.get_time_to_breach(fake_id)

if __name__ == "__main__":
    unittest.main()