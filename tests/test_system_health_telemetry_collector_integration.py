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
        self.test_dir = f"/tmp/test_telemetry_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.report_path = os.path.join(self.test_dir, f"report_{uuid.uuid4().hex}.json")
        self.dashboard_path = os.path.join(self.test_dir, f"dashboard_{uuid.uuid4().hex}.json")

    def tearDown(self):
        for path in [self.report_path, self.dashboard_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_collect_and_process_telemetry_integration(self):
        module_name = f"module_{uuid.uuid4().hex[:8]}"
        rand_metric = random.randint(100, 9999)
        incident_data = {"incident_id": str(uuid.uuid4()), "load": rand_metric}
        audit_summary = {"status": "checked", "errors": random.randint(0, 5)}
        metrics = {"cpu_usage": random.random(), "memory_usage": random.random()}
        dashboard_format = f"format_{uuid.uuid4().hex[:4]}"
        incidents_list = [str(uuid.uuid4()), str(uuid.uuid4())]
        patches_list = [f"patch_{random.randint(1, 100)}"]

        stream_data = f"stream_payload_{uuid.uuid4().hex}"
        stream_result = self.streamer.stream_data(stream_data, self.report_path)

        result = self.collector.collect_and_process_telemetry(
            module_name,
            incident_data,
            audit_summary,
            metrics,
            dashboard_format,
            incidents_list,
            patches_list,
            self.report_path,
            self.dashboard_path
        )

        self.assertIn(module_name, result)
        self.assertTrue(os.path.exists(self.report_path), "Report file must be created by telemetry ingestion")
        
        with open(self.report_path, 'r') as f:
            file_content = json.load(f)
            self.assertIn(module_name, file_content)
            self.assertEqual(file_content.get("status"), "OK")

if __name__ == '__main__':
    unittest.main()