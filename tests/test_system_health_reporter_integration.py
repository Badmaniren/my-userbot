import unittest
import os
import uuid
import random
import io
import json
from skills.system_health_reporter import SystemHealthReporter
from skills.system_health_aggregator import SystemHealthAggregator
from skills.recovery_report_exporter import RecoveryReportExporter

class TestSystemHealthReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.reporter = SystemHealthReporter()
        self.aggregator = SystemHealthAggregator()
        self.exporter = RecoveryReportExporter()
        self.test_dir = f"test_dir_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_full_health_reporting_pipeline_integration(self):
        random_module = f"module_{uuid.uuid4().hex[:8]}"
        random_incident_id = f"INC-{random.randint(1000, 9999)}"
        random_error_msg = f"Error code {random.randint(500, 599)}"
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        
        incident_data = {
            "incident_id": random_incident_id,
            "error": random_error_msg,
            "severity": random_severity
        }
        
        audit_summary = {
            "vulnerabilities_found": random.randint(0, 10),
            "status": "passed"
        }
        
        metrics = {
            "cpu_usage": round(random.uniform(10.0, 99.0), 2),
            "memory_usage": round(random.uniform(20.0, 90.0), 2)
        }

        health_report_json = self.reporter.generate_health_report(
            module_name=random_module,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics
        )
        
        parsed_report = json.loads(health_report_json)
        self.assertEqual(parsed_report["module"], random_module)
        self.assertEqual(parsed_report["metrics"]["incident_id"], random_incident_id)
        self.assertEqual(parsed_report["metrics"]["error"], random_error_msg)
        self.assertEqual(parsed_report["metrics"]["severity"], random_severity)

        file_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")
        export_result = self.reporter.export_health_report(parsed_report, file_path)
        self.assertTrue(export_result)
        self.assertTrue(os.path.exists(file_path))

        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = json.load(f)
        self.assertEqual(file_content["metrics"]["incident_id"], random_incident_id)

        stream_data = io.BytesIO(f"Telemetry stream {uuid.uuid4().hex}".encode('utf-8'))
        stream_parsed = self.reporter.parse_stream_data(stream_data)
        self.assertIsNotNone(stream_parsed)
        self.assertIn("raw_length", stream_parsed)
        self.assertGreater(stream_parsed["raw_length"], 0)

        incidents_list = [random_incident_id for _ in range(random.randint(1, 5))]
        patches_list = [f"patch_{uuid.uuid4().hex[:4]}" for _ in range(random.randint(1, 5))]
        aggregated_metrics = self.reporter.aggregate_system_metrics(incidents_list, patches_list)
        self.assertEqual(aggregated_metrics["total_incidents"], len(incidents_list))
        self.assertEqual(aggregated_metrics["total_patches"], len(patches_list))

        comprehensive_report = self.exporter.generate_comprehensive_report(
            module_name=random_module,
            exception=Exception(random_error_msg),
            traceback_str="Traceback dummy",
            incident_id=random_incident_id,
            audit_data=audit_summary
        )
        self.assertIsInstance(comprehensive_report, dict)

        epic_id = f"EPIC-{random.randint(100, 999)}"
        export_epic_path = os.path.join(self.test_dir, f"epic_{uuid.uuid4().hex}.json")
        epic_export_result = self.exporter.export_epic_report_file(comprehensive_report, export_epic_path)
        self.assertTrue(epic_export_result)
        self.assertTrue(os.path.exists(export_epic_path))

if __name__ == '__main__':
    unittest.main()