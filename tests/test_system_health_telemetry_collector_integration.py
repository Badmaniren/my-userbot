import unittest
import os
import uuid
import random
import json
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector

class TestSystemHealthTelemetryCollectorIntegration(unittest.TestCase):
    def setUp(self):
        self.collector = SystemHealthTelemetryCollector()
        self.test_uuid = str(uuid.uuid4())
        self.module_name = f"module_{self.test_uuid[:8]}"
        self.report_path = f"test_report_{self.test_uuid}.json"
        self.dashboard_path = f"test_dashboard_{self.test_uuid}.json"

    def tearDown(self):
        for path in [self.report_path, self.dashboard_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_collect_and_process_telemetry_integration(self):
        random_metric_value = random.randint(100, 999)
        incident_data = {"incident_id": self.test_uuid, "severity": "HIGH"}
        audit_summary = {"status": "PASSED", "score": random_metric_value}
        metrics = {"cpu_load": random.random(), "memory_usage": random_metric_value}
        dashboard_format = "json"
        incidents_list = [f"inc_{random.randint(1, 1000)}"]
        patches_list = [f"patch_{random.randint(1, 1000)}"]

        result = self.collector.collect_and_process_telemetry(
            self.module_name,
            incident_data,
            audit_summary,
            metrics,
            dashboard_format,
            incidents_list,
            patches_list,
            self.report_path,
            self.dashboard_path
        )

        self.assertIsInstance(result, dict)
        self.assertIn(self.module_name, result)
        
        self.assertTrue(os.path.exists(self.report_path), "Report file was not created by real integration workflow.")
        
        with open(self.report_path, 'r') as f:
            file_content = json.load(f)
            self.assertIn(self.module_name, file_content)
            self.assertEqual(file_content.get("status"), "OK")

    def test_process_telemetry_stream_integration(self):
        stream_data = f"STREAM_DATA_{self.test_uuid}"
        stream_path = f"stream_{self.test_uuid}.log"

        try:
            result = self.collector.process_telemetry_stream(stream_data, stream_path)
            self.assertIsNotNone(result)
        finally:
            if os.path.exists(stream_path):
                os.remove(stream_path)

if __name__ == '__main__':
    unittest.main()