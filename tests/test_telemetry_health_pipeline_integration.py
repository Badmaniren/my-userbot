import unittest
import uuid
import random
import os
import tempfile

from skills.telemetry_health_pipeline import run_telemetry_health_pipeline


class TestTelemetryHealthPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.stream_path = os.path.join(self.test_dir.name, f"stream_{uuid.uuid4()}.json")
        self.report_path = os.path.join(self.test_dir.name, f"report_{uuid.uuid4()}.json")
        self.dashboard_path = os.path.join(self.test_dir.name, f"dashboard_{uuid.uuid4()}.json")

        self.module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.metric_value = random.randint(100, 1000)
        self.incident_id = str(uuid.uuid4())

        import json
        sample_data = [
            {
                "timestamp": 1600000000 + random.randint(1, 100),
                "metric": "cpu_load",
                "value": self.metric_value,
                "status": "active",
                "incident_id": self.incident_id
            }
        ]
        with open(self.stream_path, "w", encoding="utf-8") as f:
            json.dump(sample_data, f)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_telemetry_health_pipeline_end_to_end(self):
        incident_data = {"id": self.incident_id, "severity": "HIGH", "source": self.module_name}
        audit_summary = {"status": "verified", "code": random.randint(200, 500)}
        metrics = {"average_load": self.metric_value}
        dashboard_format = "json"
        incidents_list = [self.incident_id]
        patches_list = [f"patch_{uuid.uuid4().hex[:6]}"]

        result = run_telemetry_health_pipeline(
            stream_path=self.stream_path,
            module_name=self.module_name,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics,
            dashboard_format=dashboard_format,
            incidents_list=incidents_list,
            patches_list=patches_list,
            report_path=self.report_path,
            dashboard_path=self.dashboard_path
        )

        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(self.report_path))
        self.assertTrue(os.path.exists(self.dashboard_path))

        import json
        with open(self.report_path, "r", encoding="utf-8") as f:
            report_content = json.load(f)
            self.assertIn(self.module_name, str(report_content))


if __name__ == "__main__":
    unittest.main()