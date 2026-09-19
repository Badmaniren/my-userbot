import unittest
import uuid
import random
import os
import tempfile
from skills.system_audit_log_exporter import export_system_audit_log
from skills.incident_aggregator import aggregate_incidents
from skills.system_health_telemetry_collector import collect_telemetry

class TestSystemAuditLogExporterIntegration(unittest.TestCase):

    def test_export_system_audit_log_integration(self):
        random_suffix = str(uuid.uuid4())
        test_incident_id = f"INC-{random.randint(10000, 99999)}-{random_suffix[:8]}"
        test_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        test_metric_value = random.uniform(10.5, 99.9)

        telemetry_data = collect_telemetry({
            "metric_id": random_suffix,
            "value": test_metric_value
        })

        incident_data = aggregate_incidents({
            "incident_id": test_incident_id,
            "severity": test_severity,
            "telemetry_ref": telemetry_data
        })

        with tempfile.TemporaryDirectory() as temp_dir:
            export_result = export_system_audit_log({
                "audit_id": random_suffix,
                "incident": incident_data,
                "output_directory": temp_dir
            })

            self.assertIsNotNone(export_result)
            self.assertIn("exported_file", export_result)
            
            exported_file_path = export_result["exported_file"]
            self.assertTrue(os.path.exists(exported_file_path))

            with open(exported_file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(test_incident_id, content)
                self.assertIn(random_suffix, content)

if __name__ == "__main__":
    unittest.main()