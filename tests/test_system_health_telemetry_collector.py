import unittest
import uuid
import random
import string
import json
import tempfile
import os
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector

class TestSystemHealthTelemetryCollector(unittest.TestCase):

    def setUp(self):
        self.collector = SystemHealthTelemetryCollector()
        self.module_name = f"mod_{uuid.uuid4().hex[:8]}"
        self.incident_data = {uuid.uuid4().hex[:6]: random.randint(1, 100)}
        self.audit_summary = f"audit_{uuid.uuid4().hex[:8]}"
        self.metrics = {uuid.uuid4().hex[:6]: random.random() for _ in range(3)}
        self.dashboard_format = random.choice(["json", "xml", "yaml", "html"])
        self.incidents_list = [uuid.uuid4().hex for _ in range(2)]
        patches_count = random.randint(1, 5)
        self.patches_list = [uuid.uuid4().hex for _ in range(patches_count)]

        self.temp_dir = tempfile.TemporaryDirectory()
        self.report_path = os.path.join(self.temp_dir.name, f"report_{uuid.uuid4().hex}.json")
        self.dashboard_path = os.path.join(self.temp_dir.name, f"dashboard_{uuid.uuid4().hex}.json")
        self.stream_path = os.path.join(self.temp_dir.name, f"stream_{uuid.uuid4().hex}.log")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_collect_and_aggregate_telemetry(self):
        result = self.collector.collect_and_aggregate_telemetry(
            self.module_name,
            self.incident_data,
            self.audit_summary,
            self.metrics,
            self.dashboard_format,
            self.incidents_list,
            self.patches_list
        )
        self.assertIsNotNone(result)
        self.assertIsInstance(result, (dict, list, str, int, float))

    def test_process_telemetry_stream(self):
        stream_content = f"telemetry_stream_{uuid.uuid4().hex}".encode('utf-8')
        with open(self.stream_path, 'wb') as f:
            f.write(stream_content)

        with open(self.stream_path, 'rb') as stream:
            result = self.collector.process_telemetry_stream(stream, self.stream_path)
            self.assertIsNotNone(result)

    def test_export_comprehensive_report(self):
        payload = {
            "id": uuid.uuid4().hex,
            "value": random.randint(100, 999)
        }
        status = self.collector.export_comprehensive_report(payload, self.dashboard_path)
        self.assertIsNotNone(status)

    def test_collect_and_process_telemetry(self):
        result = self.collector.collect_and_process_telemetry(
            self.module_name,
            self.incident_data,
            self.audit_summary,
            self.metrics,
            self.dashboard_format,
            self.incidents_list,
            self.patches_list,
            self.report_path,
            self.dashboard_path
        )

        self.assertIn(self.module_name, result)
        self.assertTrue(os.path.exists(self.report_path))

        with open(self.report_path, 'r') as f:
            data = json.load(f)
            self.assertIn(self.module_name, data)
            self.assertEqual(data.get("status"), "OK")

if __name__ == '__main__':
    unittest.main()