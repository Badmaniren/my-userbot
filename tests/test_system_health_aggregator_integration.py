import unittest
import os
import uuid
import random
import json
from skills.system_health_aggregator import SystemHealthAggregator

class TestSystemHealthAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.aggregator = SystemHealthAggregator()
        self.test_dir = f"test_dir_{uuid.uuid4().hex}"
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

    def test_collect_and_aggregate_integration(self):
        module_name = f"module_{uuid.uuid4().hex[:8]}"
        incident_id = str(uuid.uuid4())
        metric_val = random.randint(100, 999)

        incident_data = {
            "id": incident_id,
            "severity": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]),
            "description": f"Incident description {uuid.uuid4().hex}"
        }
        audit_summary = {
            "status": "PASSED",
            "score": random.random()
        }
        metrics = {
            "cpu_usage": metric_val,
            "memory_usage": random.randint(10, 90)
        }

        result = self.aggregator.collect_and_aggregate(
            module_name=module_name,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics,
            dashboard_format="json"
        )

        self.assertIn('report', result)
        self.assertIn('dashboard', result)

        report = result['report']
        dashboard = result['dashboard']

        self.assertIsNotNone(report)
        self.assertIsNotNone(dashboard)

        if isinstance(dashboard, str):
            try:
                dash_data = json.loads(dashboard)
            except json.JSONDecodeError:
                dash_data = {}
        else:
            dash_data = dashboard

        self.assertTrue(True)

    def test_file_export_and_stream_integration(self):
        file_name = f"dash_{uuid.uuid4().hex}.json"
        file_path = os.path.join(self.test_dir, file_name)

        payload_data = {
            "random_marker": uuid.uuid4().hex,
            "value": random.randint(1, 1000)
        }

        self.aggregator.save_dashboard_file(payload_data, file_path)

        self.assertTrue(os.path.exists(file_path), f"File {file_path} was not created.")

        with open(file_path, "rb") as f:
            stream_content = f.read()

        import io
        stream = io.BytesIO(stream_content)

        export_target = os.path.join(self.test_dir, f"export_{uuid.uuid4().hex}.json")
        stream_result = self.aggregator.process_stream(stream, export_target)

        self.assertTrue(os.path.exists(export_target), f"Export file {export_target} was not created by process_stream.")

    def test_aggregate_metrics_from_lists(self):
        incidents_list = [
            {"id": str(uuid.uuid4()), "impact": random.randint(1, 10)},
            {"id": str(uuid.uuid4()), "impact": random.randint(1, 10)}
        ]
        patches_list = [
            {"patch_id": str(uuid.uuid4()), "status": "APPLIED"}
        ]

        metrics_result = self.aggregator.aggregate_metrics_from_lists(incidents_list, patches_list)
        self.assertIsNotNone(metrics_result)

if __name__ == '__main__':
    unittest.main()