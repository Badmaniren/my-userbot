import unittest
import os
import uuid
import random
import json
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector
from skills.telemetry_streamer import TelemetryStreamer

class TestSystemHealthTelemetryCollectorIntegration(unittest.TestCase):
    def setUp(self):
        self.collector = SystemHealthTelemetryCollector()
        self.streamer = TelemetryStreamer()
        self.test_dir = f"test_telemetry_dir_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        for filename in os.listdir(self.test_dir):
            file_path = os.path.join(self.test_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_collect_and_process_telemetry_integration(self):
        module_name = f"module_{uuid.uuid4().hex[:8]}"
        incident_id = str(uuid.uuid4())
        metric_value = random.randint(100, 1000)

        incident_data = {"incident_id": incident_id, "severity": "HIGH"}
        audit_summary = {"status": "PASSED", "checks": random.randint(5, 20)}
        metrics = {"cpu_usage": metric_value, "memory_usage": random.randint(20, 80)}
        dashboard_format = "json"
        incidents_list = [incident_id]
        patches_list = [f"patch_{uuid.uuid4().hex[:6]}"]

        report_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")
        dashboard_path = os.path.join(self.test_dir, f"dashboard_{uuid.uuid4().hex}.json")

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

        self.assertIn(module_name, result)
        self.assertTrue(os.path.exists(report_path), "Report file must be created")
        self.assertTrue(os.path.exists(dashboard_path), "Dashboard file must be created")

        with open(report_path, 'r') as f:
            report_content = json.load(f)
            self.assertIn(module_name, report_content)
            self.assertEqual(report_content.get("status"), "OK")

    def test_process_telemetry_stream_integration(self):
        stream_name = f"stream_{uuid.uuid4().hex[:8]}"
        stream_data = f"data_metric_{random.randint(1000, 9999)}"
        stream_path = os.path.join(self.test_dir, f"stream_{uuid.uuid4().hex}.log")

        with open(stream_path, 'w') as f:
            f.write(stream_data)

        stream_result = self.collector.process_telemetry_stream(stream_name, stream_path)
        self.assertIsNotNone(stream_result)

if __name__ == '__main__':
    unittest.main()