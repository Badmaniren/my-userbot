import unittest
import os
import uuid
import random
import tempfile
from skills.telemetry_health_pipeline import run_telemetry_health_pipeline

class TestTelemetryHealthPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.source_path = os.path.join(self.temp_dir.name, f"source_{uuid.uuid4()}.json")
        self.report_path = os.path.join(self.temp_dir.name, f"report_{uuid.uuid4()}.json")

        self.random_device_id = f"device-{uuid.uuid4()}"
        self.random_cpu_load = round(random.uniform(10.0, 99.9), 2)

        raw_data = (
            '{'
            f'"device_id": "{self.random_device_id}", '
            f'"cpu_load": {self.random_cpu_load}, '
            '"status": "active"'
            '}'
        )
        with open(self.source_path, 'w', encoding='utf-8') as f:
            f.write(raw_data)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pipeline_real_integration(self):
        module_name = f"mod_{uuid.uuid4()}"
        incident_data = {"id": str(uuid.uuid4()), "severity": random.choice(["LOW", "MEDIUM", "HIGH"])}
        audit_summary = {"checked": random.randint(1, 100)}
        metrics = {"latency": random.random()}
        dashboard_format = random.choice(["json", "html"])
        incidents_list = [incident_data["id"]]
        patches_list = [f"patch-{uuid.uuid4()}"]

        result = run_telemetry_health_pipeline(
            source_path=self.source_path,
            report_path=self.report_path,
            module_name=module_name,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics,
            dashboard_format=dashboard_format,
            incidents_list=incidents_list,
            patches_list=patches_list
        )

        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(self.report_path))

        with open(self.report_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(self.random_device_id, content)

if __name__ == '__main__':
    unittest.main()