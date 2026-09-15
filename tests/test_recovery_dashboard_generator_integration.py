import unittest
import uuid
import random
import os
import json

from skills.error_recovery_hub import ErrorRecoveryHub
from skills.incident_aggregator import IncidentAggregator
from skills.recovery_report_exporter import RecoveryReportExporter
from skills.dependency_audit_reporter import DependencyAuditReporter
from skills.recovery_dashboard_generator import RecoveryDashboardGenerator

class TestRecoveryDashboardGeneratorIntegration(unittest.TestCase):

    def test_dashboard_generation_end_to_end(self):
        module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        exception_msg = f"RandomError_{uuid.uuid4().hex[:6]}"
        tb_str = f"Traceback (most recent call last):\n  File '{module_name}.py', line {random.randint(1, 100)}\n    raise {exception_msg}"
        incident_id = str(uuid.uuid4())
        epic_id = f"EPIC-{random.randint(1000, 9999)}"

        hub = ErrorRecoveryHub()
        captured_id = hub.capture_failure(module_name, Exception(exception_msg), tb_str)
        self.assertIsNotNone(captured_id)

        aggregator = IncidentAggregator()
        aggregated_data = aggregator.process_and_aggregate(module_name, Exception(exception_msg), tb_str, incident_id)

        audit_data = {
            "epic_id": epic_id,
            "module": module_name,
            "status": "audited",
            "vulnerabilities": random.randint(0, 5)
        }

        reporter = RecoveryReportExporter()
        comprehensive_report = reporter.generate_comprehensive_report(
            module_name=module_name,
            exception=Exception(exception_msg),
            traceback_str=tb_str,
            incident_id=incident_id,
            audit_data=audit_data
        )
        self.assertIsNotNone(comprehensive_report)

        dep_reporter = DependencyAuditReporter()
        summary_payload = {
            "epic_id": epic_id,
            "metrics": {
                "total_incidents": random.randint(1, 50),
                "resolved": random.randint(1, 50)
            }
        }
        exported_summary = dep_reporter.export_summary(summary_payload, format="json")
        self.assertIsNotNone(exported_summary)

        dashboard_generator = RecoveryDashboardGenerator()
        
        metrics_input = {
            "module": module_name,
            "error_rate": random.random(),
            "incidents_count": random.randint(1, 100)
        }
        
        dashboard_output = dashboard_generator.generate_dashboard(
            metrics=metrics_input,
            incidents=[aggregated_data],
            reports=[exported_summary]
        )

        self.assertIsNotNone(dashboard_output)
        
        if isinstance(dashboard_output, str):
            self.assertTrue(len(dashboard_output) > 0)
            if dashboard_output.strip().startswith("{") or dashboard_output.strip().startswith("["):
                parsed = json.loads(dashboard_output)
                self.assertIsInstance(parsed, (dict, list))
        elif isinstance(dashboard_output, dict):
            self.assertIn("metrics", dashboard_output)

        output_file_path = f"dashboard_{uuid.uuid4().hex}.html"
        try:
            saved_status = dashboard_generator.export_dashboard_file(dashboard_output, output_file_path)
            if saved_status is True or isinstance(saved_status, str):
                self.assertTrue(os.path.exists(output_file_path))
                self.assertGreater(os.path.getsize(output_file_path), 0)
        finally:
            if os.path.exists(output_file_path):
                os.remove(output_file_path)

if __name__ == "__main__":
    unittest.main()