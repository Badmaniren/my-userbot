import unittest
import uuid
import os
import json
from skills.incident_sla_audit_report_exporter import incident_sla_audit_report_exporter

class TestIncidentSlaAuditReportExporterIntegration(unittest.TestCase):
    def test_integration_export_config_pipeline(self):
        unique_report_id = f"rep-{uuid.uuid4()}"
        unique_incident_id = f"inc-{uuid.uuid4()}"
        unique_namespace = f"ns-{uuid.uuid4()}"

        export_config = {
            "report_id": unique_report_id,
            "sla_data": {
                "incident_id": unique_incident_id,
                "namespace": unique_namespace,
                "compliance_check": True
            }
        }

        result = incident_sla_audit_report_exporter(export_config=export_config)

        self.assertIsInstance(result, dict)
        self.assertIn("report_path", result)
        self.assertIn("target_incident_id", result)

        report_path = result["report_path"]
        target_incident_id = result["target_incident_id"]

        self.assertEqual(target_incident_id, unique_incident_id)
        self.assertTrue(os.path.exists(report_path))

        try:
            with open(report_path, "r", encoding="utf-8") as f:
                content = json.load(f)

            self.assertEqual(content.get("report_id"), unique_report_id)
            self.assertEqual(content.get("target_incident_id"), unique_incident_id)
            self.assertIn("sla_data", content)
            self.assertEqual(content["sla_data"].get("namespace"), unique_namespace)
        finally:
            if os.path.exists(report_path):
                os.remove(report_path)

if __name__ == "__main__":
    unittest.main()