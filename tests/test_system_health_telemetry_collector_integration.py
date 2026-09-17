import unittest
import os
import uuid
import random
import json
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector


class TestSystemHealthTelemetryCollectorIntegration(unittest.TestCase):

    def setUp(self):
        self.collector = SystemHealthTelemetryCollector()
        self.test_dir = f"test_telemetry_{uuid.uuid4().hex}"
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
        metrics = {"cpu_usage": metric_value, "memory_usage": random.random()}
        dashboard_format = "json"
        incidents_list = [incident_id]
        patches_list = [f"patch_{uuid.uuid4().hex[:6]}"]

        report_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")
        dashboard_path = os.path.join(self.test_dir, f"dashboard_{uuid.uuid4().hex}.json")

        result = self.collector.collect_and_process_telemetry(
            module_name=module_name,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics,
            dashboard_format=dashboard_format,
            incidents_list=incidents_list,
            patches_list=patches_list,
            report_path=report_path,
            dashboard_path=dashboard_path
        )

        self.assertIn(module_name, result)
        self.assertTrue(os.path.exists(report_path), "Файл отчета не был создан")
        
        with open(report_path, 'r') as f:
            file_content = json.load(f)
            self.assertIn(module_name, file_content)
            self.assertEqual(file_content.get("status"), "OK")

    def test_process_stream_integration(self):
        stream_id = uuid.uuid4().hex
        stream = [
            {"stream_id": stream_id, "timestamp": random.randint(1000000, 9999999), "value": random.random()}
        ]
        path = os.path.join(self.test_dir, f"stream_{uuid.uuid4().hex}.json")

        stream_result = self.collector.process_stream(stream, path)
        self.assertIsNotNone(stream_result)


if __name__ == "__main__":
    unittest.main()