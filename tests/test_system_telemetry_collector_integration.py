import unittest
import uuid
import random
import os
import tempfile
from skills.system_telemetry_collector import SystemTelemetryCollector
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.dependency_audit_reporter import DependencyAuditReporter
from skills.patch_scheduler import PatchScheduler

class TestSystemTelemetryCollectorIntegration(unittest.TestCase):
    def setUp(self):
        self.telemetry_collector = SystemTelemetryCollector()
        self.recovery_hub = ErrorRecoveryHub()
        self.audit_reporter = DependencyAuditReporter()
        self.patch_scheduler = PatchScheduler()
        self.test_module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.test_incident_id = str(uuid.uuid4())
        self.test_exception_msg = f"Random error {uuid.uuid4()}"

    def test_telemetry_collection_and_reliability_analysis(self):
        random_value = random.randint(100, 999)
        exception_instance = RuntimeError(f"{self.test_exception_msg}_{random_value}")
        
        incident_id = self.recovery_hub.capture_failure(
            module_name=self.test_module_name,
            exception=exception_instance,
            traceback_str="Traceback (most recent call last):\n  File 'test.py', line 1"
        )
        
        self.assertIsNotNone(incident_id)
        
        incident_history = self.recovery_hub.get_incident_history(self.test_module_name)
        self.assertIsInstance(incident_history, list)
        
        audit_data = {
            "incident_id": incident_id,
            "module": self.test_module_name,
            "metric": random_value
        }
        report_str = self.audit_reporter.generate_report(audit_data)
        self.assertIsInstance(report_str, str)
        
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"report_{uuid.uuid4().hex}.json")
        export_success = self.audit_reporter.generate_epic_report(audit_data, output_path)
        self.assertTrue(export_success)
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(incident_id, file_content)
        
        os.remove(output_path)
        
        telemetry_payload = {
            "incident_id": incident_id,
            "module_name": self.test_module_name,
            "error_message": str(exception_instance),
            "random_marker": random_value
        }
        
        if hasattr(self.telemetry_collector, "collect_metrics"):
            telemetry_result = self.telemetry_collector.collect_metrics(telemetry_payload)
            self.assertIsNotNone(telemetry_result)
        elif hasattr(self.telemetry_collector, "record_telemetry"):
            telemetry_result = self.telemetry_collector.record_telemetry(telemetry_payload)
            self.assertIsNotNone(telemetry_result)
        elif hasattr(self.telemetry_collector, "send_telemetry"):
            telemetry_result = self.telemetry_collector.send_telemetry(telemetry_payload)
            self.assertIsNotNone(telemetry_result)
        else:
            telemetry_result = self.telemetry_collector(telemetry_payload)
            self.assertIsNotNone(telemetry_result)

if __name__ == "__main__":
    unittest.main()