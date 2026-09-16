import unittest
import uuid
import random
from skills.incident_sla_compliance_monitor import monitor_incident_sla_compliance
from skills.incident_sla_tracker import track_incident_sla
from skills.incident_sla_mitigation_planner import plan_incident_sla_mitigation

class TestIncidentSlaComplianceMonitorIntegration(unittest.TestCase):
    def test_sla_compliance_monitor_integration(self):
        random_incident_id = f"INC-{uuid.uuid4()}"
        random_threshold_minutes = random.randint(15, 120)
        random_elapsed_time = random_threshold_minutes + random.randint(5, 60)

        tracking_result = track_incident_sla(
            incident_id=random_incident_id,
            threshold_minutes=random_threshold_minutes,
            elapsed_minutes=random_elapsed_time
        )

        self.assertIsNotNone(tracking_result)
        self.assertIn("breach_detected", tracking_result)
        self.assertTrue(tracking_result["breach_detected"])

        mitigation_plan = plan_incident_sla_mitigation(
            incident_id=random_incident_id,
            breach_data=tracking_result
        )

        self.assertIsNotNone(mitigation_plan)
        self.assertIn("mitigation_steps", mitigation_plan)

        compliance_report = monitor_incident_sla_compliance(
            incident_id=random_incident_id,
            tracker_data=tracking_result,
            mitigation_data=mitigation_plan
        )

        self.assertIsNotNone(compliance_report)
        self.assertEqual(compliance_report.get("incident_id"), random_incident_id)
        self.assertEqual(compliance_report.get("status"), "MONITORED_BREACH")
        self.assertIn("timestamp", compliance_report)

if __name__ == "__main__":
    unittest.main()