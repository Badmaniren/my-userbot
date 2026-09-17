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

        self.report_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")
        self.dashboard_path = os.path.join(self.test_dir, f"dashboard_{uuid.uuid4().hex}.json")
        self.stream_path = os.path.join(self.test_dir, f"stream_{uuid.uuid4().hex}.log")

    def tearDown(self):
        for path in [self.report_path, self.dashboard_path, self.stream_path]:
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_collect_and_process_telemetry_integration(self):
        module_name = f"mod_{uuid.uuid4().hex[:8]}"
        random_id = str(uuid.uuid4())
        random_metric_value = random.randint(100, 999)

        incident_data = {"incident_id": random_id, "severity": "HIGH"}
        audit_summary = {"status": "checked", "errors_found": random.randint(0, 5)}
        metrics = {"cpu_load": random_metric_value, "memory_usage": random.random()}
        dashboard_format = "json"
        incidents_list = [random_id]
        patches_list = [f"patch_{uuid.uuid4().hex[:4]}"]

        result = self.collector.collect_and_process_telemetry(
            module_name=module_name,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics,
            dashboard_format=dashboard_format,
            incidents_list=incidents_list,
            patches_list=patches_list,
            report_path=self.report_path,
            dashboard_path=self.dashboard_path
        )

        self.assertIn(module_name, result)
        self.assertTrue(os.path.exists(self.report_path), "Report file must be created")
        self.assertTrue(os.path.exists(self.dashboard_path), "Dashboard file must be created")

        with open(self.report_path, 'r') as f:
            file_data = json.load(f)
            self.assertIn(module_name, file_data)
            self.assertEqual(file_data.get("status"), "OK")

    def test_process_telemetry_stream_integration(self):
        stream_data = f"telemetry_stream_payload_{uuid.uuid4().hex}"
        stream_result = self.collector.process_stream_data(stream_data, self.stream_path)
        self.assertIsNotNone(stream_result)


if __name__ == '__main__':
    unittest.main()