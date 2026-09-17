import unittest
import os
import uuid
import random
import io
import json
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector

class TestSystemHealthTelemetryCollectorIntegration(unittest.TestCase):
    def setUp(self):
        self.collector = SystemHealthTelemetryCollector()
        self.test_dir = f"test_telemetry_dir_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                try:
                    os.remove(os.path.join(root, name))
                except OSError:
                    pass
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except OSError:
                    pass
        try:
            os.rmdir(self.test_dir)
        except OSError:
            pass

    def test_collect_and_aggregate_telemetry_integration(self):
        module_name = f"module_{uuid.uuid4().hex[:8]}"
        random_metric_val = random.randint(100, 999)
        incident_data = {"id": str(uuid.uuid4()), "severity": "HIGH"}
        audit_summary = {"status": "PASSED", "score": random.random()}
        metrics = {"cpu_usage": random_metric_val}
        dashboard_format = "json"
        incidents_list = [str(uuid.uuid4())]
        patches_list = [str(uuid.uuid4())]

        result = self.collector.collect_and_aggregate_telemetry(
            module_name,
            incident_data,
            audit_summary,
            metrics,
            dashboard_format,
            incidents_list,
            patches_list
        )

        self.assertIsNotNone(result)
        self.assertIsInstance(result, (dict, list, str, int, float))

    def test_process_telemetry_stream_integration(self):
        stream_content = f"telemetry_stream_data_{uuid.uuid4().hex}"
        stream_path = os.path.join(self.test_dir, f"stream_{uuid.uuid4().hex}.log")
        
        result = self.collector.process_telemetry_stream(stream_content, stream_path)
        self.assertIsNotNone(result)

    def test_export_comprehensive_report_integration(self):
        payload = {"telemetry_run_id": str(uuid.uuid4()), "value": random.randint(1, 500)}
        export_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")

        status = self.collector.export_comprehensive_report(payload, export_path)
        self.assertIsNotNone(status)

    def test_collect_and_process_telemetry_end_to_end(self):
        module_name = f"mod_{uuid.uuid4().hex[:6]}"
        incident_data = {"incident_id": str(uuid.uuid4())}
        audit_summary = {"audit": "clean"}
        metrics = {"load": random.uniform(0.1, 0.9)}
        dashboard_format = "summary"
        incidents_list = []
        patches_list = []
        
        report_path = os.path.join(self.test_dir, f"e2e_report_{uuid.uuid4().hex}.json")
        dashboard_path = os.path.join(self.test_dir, f"e2e_dashboard_{uuid.uuid4().hex}.json")

        result = self.collector.collect_and_process_telemetry(
            module_name,
            incident_data,
            audit_summary,
            metrics,
            dashboard_format,
            incidents_list,
            patches_list,
            report_path,
            dashboard_path
        )

        self.assertIsInstance(result, dict)
        self.assertIn(module_name, result)
        
        self.assertTrue(os.path.exists(report_path), "Report file must be created by the telemetry pipeline")
        
        with open(report_path, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
            self.assertIn("status", file_data)
            self.assertEqual(file_data["status"], "OK")
            self.assertIn(module_name, file_data)

if __name__ == '__main__':
    unittest.main()