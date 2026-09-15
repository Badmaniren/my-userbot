import unittest
import uuid
import random
import os
import tempfile
from skills.incident_digest_generator import IncidentDigestGenerator
from skills.error_recovery_hub import ErrorRecoveryHub
from skills.incident_aggregator import IncidentAggregator
from skills.recovery_report_exporter import RecoveryReportExporter

class TestIncidentDigestGeneratorIntegration(unittest.TestCase):

    def setUp(self):
        self.digest_generator = IncidentDigestGenerator()
        self.recovery_hub = ErrorRecoveryHub()
        self.aggregator = IncidentAggregator()
        self.report_exporter = RecoveryReportExporter()
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_digest_generation_real_flow(self):
        module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        exception_msg = f"RuntimeError_{random.randint(1000, 9999)}"
        traceback_str = f"Traceback (most recent call last):\n  File '{module_name}.py', line {random.randint(1, 100)}\n    raise {exception_msg}"
        incident_id = str(uuid.uuid4())

        capture_result = self.recovery_hub.capture_failure(module_name, Exception(exception_msg), traceback_str)
        
        aggregated_data = self.aggregator.process_and_aggregate(module_name, Exception(exception_msg), traceback_str, incident_id)
        self.assertIsNotNone(aggregated_data)

        audit_data = {
            "incident_id": incident_id,
            "module": module_name,
            "status": "processed",
            "score": random.uniform(50.0, 100.0)
        }
        
        comprehensive_report = self.report_exporter.generate_comprehensive_report(
            module_name=module_name,
            exception=Exception(exception_msg),
            traceback_str=traceback_str,
            incident_id=incident_id,
            audit_data=audit_data
        )
        self.assertIsNotNone(comprehensive_report)

        digest_payload = {
            "incident_id": incident_id,
            "module_name": module_name,
            "error": exception_msg,
            "report": comprehensive_report
        }

        output_filename = f"digest_{uuid.uuid4().hex}.json"
        output_path = os.path.join(self.test_dir.name, output_filename)

        if hasattr(self.digest_generator, "generate_digest"):
            digest_result = self.digest_generator.generate_digest(digest_payload)
            self.assertIsNotNone(digest_result)

        if hasattr(self.digest_generator, "export_digest_file"):
            export_success = self.digest_generator.export_digest_file(digest_payload, output_path)
            self.assertTrue(export_success)
            self.assertTrue(os.path.exists(output_path))
            
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(incident_id, content)
                self.assertIn(module_name, content)

if __name__ == "__main__":
    unittest.main()