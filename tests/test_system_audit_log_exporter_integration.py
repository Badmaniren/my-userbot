import unittest
import os
import json
import uuid
import random
from skills.system_audit_log_exporter import SystemAuditLogExporter, export_system_audit_log
from skills.incident_aggregator import aggregate_incidents
from skills.system_health_telemetry_collector import collect_telemetry

class TestSystemAuditLogExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.exporter = SystemAuditLogExporter()
        self.test_dir = f"./test_audit_output_{uuid.uuid4().hex}"

    def tearDown(self):
        if os.path.exists(self.test_dir):
            for f in os.listdir(self.test_dir):
                file_path = os.path.join(self.test_dir, f)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            os.rmdir(self.test_dir)

    def test_export_system_audit_log_integration(self):
        audit_id = f"aud-{uuid.uuid4().hex[:8]}"
        random_value = random.randint(1000, 99999)

        raw_incident = {
            "incident_id": f"inc-{uuid.uuid4().hex[:6]}",
            "severity_score": random_value,
            "description": "Integration test incident data"
        }

        try:
            aggregated = aggregate_incidents([raw_incident])
        except Exception:
            aggregated = raw_incident

        try:
            telemetry = collect_telemetry()
        except Exception:
            telemetry = {"status": "active"}

        payload = {
            "audit_id": audit_id,
            "incident": aggregated,
            "telemetry": telemetry,
            "output_directory": self.test_dir
        }

        result = export_system_audit_log(payload)

        self.assertIn("exported_file", result)
        file_path = result["exported_file"]
        self.assertTrue(os.path.exists(file_path))

        with open(file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data.get("audit_id"), audit_id)
        self.assertIn("incident", file_data)
        self.assertEqual(file_data["incident"].get("severity_score"), random_value)

    def test_format_standardized_logs_integration(self):
        record_id = uuid.uuid4().hex
        random_metric = random.random()

        audit_records = [
            {
                "record_id": record_id,
                "metric": random_metric,
                "source": "integration_test_suite"
            }
        ]

        formatted_json_str = self.exporter.format_standardized_logs(audit_records)
        parsed = json.loads(formatted_json_str)

        self.assertIn("records", parsed)
        self.assertEqual(len(parsed["records"]), 1)
        self.assertEqual(parsed["records"][0]["record_id"], record_id)
        self.assertEqual(parsed["records"][0]["metric"], random_metric)

if __name__ == "__main__":
    unittest.main()