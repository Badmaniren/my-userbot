import unittest
import uuid
import random
import tempfile
import os
from pathlib import Path
from skills.telemetry_audit_report_exporter import TelemetryAuditReportExporter
from skills.telemetry_anomaly_audit_bridge import TelemetryAnomalyAuditBridge
from skills.recovery_report_exporter import RecoveryReportExporter

class TestTelemetryAuditReportExporterIntegration(unittest.TestCase):
    def setUp(self):
        self.workspace_dir = tempfile.mkdtemp()
        self.export_dir = tempfile.mkdtemp()
        
        self.bridge = TelemetryAnomalyAuditBridge(
            workspace_dir=self.workspace_dir,
            lifecycle_bridge=None,
            audit_reporter=None
        )
        self.exporter = RecoveryReportExporter()
        
        self.composite_module = TelemetryAuditReportExporter(
            anomaly_audit_bridge=self.bridge,
            recovery_report_exporter=self.exporter
        )

    def tearDown(self):
        for folder in (self.workspace_dir, self.export_dir):
            for root, dirs, files in os.walk(folder, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(folder)

    def test_comprehensive_audit_and_export_composition(self):
        epic_id = f"epic-{uuid.uuid4()}"
        incident_id = f"inc-{uuid.uuid4()}"
        module_name = f"telemetry_module_{random.randint(1000, 9999)}"
        
        telemetry_payload = {
            "metric": f"cpu_load_{random.randint(1, 100)}",
            "value": random.uniform(85.0, 99.9),
            "status": "ANOMALY_CRITICAL"
        }
        
        audit_data = {
            "check_id": str(uuid.uuid4()),
            "passed": False,
            "error_message": "Threshold exceeded in integration test"
        }

        output_file_path = os.path.join(self.export_dir, f"report_{uuid.uuid4()}.json")

        result_payload = self.composite_module.process_and_export_audit_report(
            telemetry_payload=telemetry_payload,
            audit_data=audit_data,
            epic_id=epic_id,
            incident_id=incident_id,
            module_name=module_name,
            output_path=output_file_path
        )

        self.assertIsNotNone(result_payload)
        self.assertIn("summary", result_payload)
        
        self.assertTrue(os.path.exists(output_file_path), "Интеграционный модуль должен создавать реальный файл отчета через композицию навыков")
        
        with open(output_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(epic_id, content)
            self.assertIn(incident_id, content)
            self.assertIn(module_name, content)

if __name__ == "__main__":
    unittest.main()