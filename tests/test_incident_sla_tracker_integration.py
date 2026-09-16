import unittest
import uuid
import random
from datetime import datetime, timedelta

from skills.incident_sla_tracker import (
    IncidentSLATracker,
    track_incident_sla
)
from skills.incident_aggregator import aggregate_incidents
from skills.incident_severity_evaluator import evaluate_incident_severity
from skills.incident_sla_mitigation_planner import plan_incident_mitigation
from skills.incident_auto_recovery_dispatcher import dispatch_auto_recovery

class IntegrationTestIncidentSLATracker(unittest.TestCase):
    def test_end_to_end_incident_sla_workflow(self):
        rand_suffix = uuid.uuid4().hex[:8]
        incident_id = f"INC-{rand_suffix}"
        severity_candidates = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        severity = random.choice(severity_candidates)

        created_at = datetime.now() - timedelta(seconds=random.randint(10, 500))
        
        agg_input = {
            "incident_id": incident_id,
            "raw_events": [{"source": "integration_test", "timestamp": created_at.timestamp()}]
        }
        aggregated_result = aggregate_incidents(agg_input)
        
        eval_input = {
            "incident_id": incident_id,
            "aggregated_data": aggregated_result
        }
        severity_result = evaluate_incident_severity(eval_input)
        
        sla_thresholds = {severity: random.randint(300, 3600) for severity in severity_candidates}
        warning_pct = 0.8
        
        tracker = IncidentSLATracker(sla_thresholds=sla_thresholds, warning_threshold_pct=warning_pct)
        tracker.register_incident(incident_id=incident_id, severity=severity, created_at=created_at)
        
        time_to_breach = tracker.get_time_to_breach(incident_id=incident_id)
        self.assertIsInstance(time_to_breach, float)

        breach_checks = tracker.check_sla_breaches()
        self.assertIsInstance(breach_checks, list)

        mitigation_input = {
            "incident_id": incident_id,
            "severity": severity,
            "time_to_breach": time_to_breach
        }
        mitigation_plan = plan_incident_mitigation(mitigation_input)
        self.assertIsNotNone(mitigation_plan)

        recovery_input = {
            "incident_id": incident_id,
            "mitigation_plan": mitigation_plan
        }
        recovery_dispatch = dispatch_auto_recovery(recovery_input)
        self.assertIsNotNone(recovery_dispatch)

        tracker.update_incident_status(incident_id=incident_id, status="RESOLVED_AUTOMATICALLY")

        sla_input = {
            "incident_id": incident_id,
            "aggregated_data": {
                "data": {
                    "timestamp": created_at.timestamp()
                }
            },
            "threshold_seconds": sla_thresholds[severity]
        }
        sla_func_result = track_incident_sla(sla_input)
        
        self.assertIn("incident_id", sla_func_result)
        self.assertEqual(sla_func_result["incident_id"], incident_id)
        self.assertIn("breach_predicted", sla_func_result)
        self.assertIn("time_remaining_seconds", sla_func_result)

if __name__ == "__main__":
    unittest.main()