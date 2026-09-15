import unittest
import uuid
import random
import os
import tempfile
from skills.recovery_report_exporter import RecoveryReportExporter
from skills.incident_aggregator import IncidentAggregator
from skills.dependency_audit_reporter import DependencyAuditReporter

class TestRecoveryReportExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.exporter = RecoveryReportExporter()
        self.aggregator = IncidentAggregator()
        self.audit_reporter = DependencyAuditReporter()
        self.test_module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.random_incident_id = str(uuid.uuid4())
        self.random_exception_msg = f"Error code {random.randint(1000, 9999)}"
        self.random_traceback = f"Traceback (most recent call last):\n  File '{self.test_module_name}.py', line {random.randint(1, 100)}\nException: {self.random_exception_msg}"

    def test_real_composition_and_export(self):
        aggregated_data = self.aggregator.process_and_aggregate(
            module_name=self.test_module_name,
            exception=Exception(self.random_exception_msg),
            traceback_str=self.random_traceback,
            incident_id=self.random_incident_id
        )
        
        self.assertIsNotNone(aggregated_data)

        audit_payload = {
            "incident_id": self.random_incident_id,
            "module": self.test_module_name,
            "error": self.random_exception_msg,
            "aggregated_info": aggregated_data,
            "metric": random.uniform(0.1, 99.9)
        }

        report_str = self.audit_reporter.generate_report(audit_payload)
        self.assertIsInstance(report_str, str)
        self.assertTrue(len(report_str) > 0)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            temp_path = tmp.name

        try:
            success = self.audit_reporter.generate_epic_report(audit_payload, temp_path)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(temp_path))
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        summary_payload = {
            "epic_id": f"epic_{uuid.uuid4().hex[:6]}",
            "incidents_count": random.randint(1, 50),
            "random_salt": uuid.uuid4().hex
        }
        
        exported_summary = self.audit_reporter.export_summary(summary_payload, format="json")
        self.assertIsInstance(exported_summary, str)
        self.assertIn(summary_payload["epic_id"], exported_summary)

if __name__ == '__main__':
    unittest.main()