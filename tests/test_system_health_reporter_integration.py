import unittest
import os
import uuid
import random
import json
import io
from skills.system_health_reporter import SystemHealthReporter

class TestSystemHealthReporterIntegration(unittest.TestCase):
    def setUp(self):
        self.reporter = SystemHealthReporter()
        self.test_dir = f"test_dir_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for file in files:
                try:
                    os.remove(os.path.join(root, file))
                except OSError:
                    pass
            try:
                os.rmdir(root)
            except OSError:
                pass

    def test_generate_and_export_health_report(self):
        module_name = f"mod_{uuid.uuid4().hex[:8]}"
        incident_id = str(uuid.uuid4())
        error_msg = f"err_{uuid.uuid4().hex[:6]}"
        severity_val = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

        incident_data = {
            "incident_id": incident_id,
            "error": error_msg,
            "severity": severity_val
        }
        audit_summary = {
            "checks_passed": random.randint(0, 100),
            "status": "OK"
        }
        metrics = {
            "cpu_load": random.uniform(0.0, 100.0)
        }

        report_str = self.reporter.generate_health_report(
            module_name=module_name,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics
        )

        self.assertIsInstance(report_str, str)
        parsed_report = json.loads(report_str)
        self.assertIn("module", parsed_report)
        self.assertEqual(parsed_report["module"], module_name)

        file_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")
        export_res = self.reporter.export_health_report(report_str, file_path)
        
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(incident_id, content)

    def test_parse_stream_data_integration(self):
        stream_content = f"LOG_DATA_{uuid.uuid4().hex}"
        stream = io.StringIO(stream_content)

        parsed = self.reporter.parse_stream_data(stream)
        self.assertIsNotNone(parsed)

    def test_aggregate_system_metrics_integration(self):
        incidents_list = [
            {"id": str(uuid.uuid4()), "severity": "HIGH", "resolved": random.choice([True, False])}
            for _ in range(random.randint(1, 5))
        ]
        patches_list = [
            {"patch_id": str(uuid.uuid4()), "success": random.choice([True, False])}
            for _ in range(random.randint(1, 5))
        ]

        aggregated = self.reporter.aggregate_system_metrics(incidents_list, patches_list)
        self.assertIsNotNone(aggregated)
        self.assertIsInstance(aggregated, (dict, list, str))

    def test_export_report_file_integration(self):
        payload = {
            "test_key": uuid.uuid4().hex,
            "metric": random.randint(100, 999)
        }
        file_path = os.path.join(self.test_dir, f"dashboard_{uuid.uuid4().hex}.json")
        
        res = self.reporter.export_report_file(payload, file_path)
        self.assertTrue(os.path.exists(file_path))
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["test_key"], payload["test_key"])

if __name__ == "__main__":
    unittest.main()