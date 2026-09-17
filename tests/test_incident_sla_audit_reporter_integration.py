import unittest
import uuid
import random
import os
from skills.incident_sla_audit_reporter import incident_sla_audit_reporter
from skills.incident_sla_tracker import incident_sla_tracker
from skills.incident_sla_breach_predictor import incident_sla_breach_predictor

class TestIncidentSlaAuditReporterIntegration(unittest.TestCase):
    def test_audit_reporter_integration_flow(self):
        incident_id = str(uuid.uuid4())
        metric_value = round(random.uniform(95.0, 99.9), 2)
        breach_probability = round(random.uniform(0.01, 0.99), 2)

        tracker_payload = {
            "incident_id": incident_id,
            "sla_metric": "resolution_time",
            "compliance_score": metric_value,
            "status": "monitored"
        }

        tracker_result = incident_sla_tracker(tracker_payload)
        self.assertIsNotNone(tracker_result)

        predictor_payload = {
            "incident_id": incident_id,
            "risk_score": breach_probability
        }

        predictor_result = incident_sla_breach_predictor(predictor_payload)
        self.assertIsNotNone(predictor_result)

        audit_payload = {
            "audit_id": str(uuid.uuid4()),
            "incident_id": incident_id,
            "tracker_data": tracker_result,
            "predictor_data": predictor_result,
            "format": "json"
        }

        report_result = incident_sla_audit_reporter(audit_payload)

        self.assertIsInstance(report_result, dict)
        self.assertIn("report_id", report_result)
        self.assertEqual(report_result["incident_id"], incident_id)
        self.assertIn("official_audit", report_result)

        if "file_path" in report_result:
            self.assertTrue(os.path.exists(report_result["file_path"]))
            os.remove(report_result["file_path"])

if __name__ == "__main__":
    unittest.main()