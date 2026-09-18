import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.incident_forensics_audit_exporter import export_forensics_audit_package

class TestIncidentForensicsAuditExporterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.incident_id = f"inc-{uuid.uuid4()}"
        self.epic_id = f"epic-{uuid.uuid4()}"
        self.module_name = f"mod-{uuid.uuid4()}"
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

        self.incident_data = {
            "incident_id": self.incident_id,
            "epic_id": self.epic_id,
            "severity": self.severity_level,
            "description": f"Random security incident {uuid.uuid4()}",
            "metrics": {
                "error_rate": random.uniform(0.01, 0.99),
                "affected_nodes": random.randint(1, 100)
            }
        }

        self.telemetry_payload = {
            "stream_id": str(uuid.uuid4()),
            "telemetry_data": {
                "cpu_load": random.randint(50, 100),
                "memory_leak_detected": random.choice([True, False])
            }
        }

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_forensics_audit_exporter_composition(self):
        destination_path = os.path.join(self.test_dir, f"forensics_package_{uuid.uuid4()}.json")

        result = export_forensics_audit_package(
            incident_data=self.incident_data,
            telemetry_payload=self.telemetry_payload,
            destination_path=destination_path,
            epic_id=self.epic_id,
            module_name=self.module_name
        )

        self.assertIsInstance(result, dict)
        self.assertTrue(os.path.exists(destination_path), "Интеграционный модуль должен создавать итоговый файл пакета доказательств.")

        self.assertIn("incident_id", result)
        self.assertEqual(result["incident_id"], self.incident_id)
        self.assertIn("epic_id", result)
        self.assertEqual(result["epic_id"], self.epic_id)

if __name__ == "__main__":
    unittest.main()