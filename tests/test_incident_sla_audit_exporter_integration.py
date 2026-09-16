import unittest
import uuid
import random
import os
from skills.incident_sla_audit_exporter import IncidentSLAAuditExporter
from skills.incident_sla_tracker import IncidentSLATracker
from skills.incident_sla_mitigation_planner import IncidentSLAMitigationPlanner

class TestIncidentSLAAuditExporterIntegration(unittest.TestCase):
    def test_export_audit_report_integration(self):
        incident_id = str(uuid.uuid4())
        sla_limit_hours = random.randint(1, 72)
        mitigation_strategy = f"strategy_{uuid.uuid4()}"

        tracker = IncidentSLATracker()
        planner = IncidentSLAMitigationPlanner()
        exporter = IncidentSLAAuditExporter()

        tracking_data = tracker.track_sla(incident_id=incident_id, limit_hours=sla_limit_hours)
        self.assertIsNotNone(tracking_data)

        mitigation_data = planner.create_plan(incident_id=incident_id, strategy=mitigation_strategy)
        self.assertIsNotNone(mitigation_data)

        report_result = exporter.export_audit_report(incident_id=incident_id)

        self.assertIsInstance(report_result, dict)
        self.assertIn("audit_id", report_result)
        self.assertEqual(report_result.get("incident_id"), incident_id)
        self.assertIn("compliance_status", report_result)

        report_file_path = report_result.get("file_path")
        if report_file_path:
            self.assertTrue(os.path.exists(report_file_path))
            os.remove(report_file_path)

if __name__ == "__main__":
    unittest.main()