import unittest
import uuid
import random
import os
import tempfile
from io import StringIO
from skills.system_health_audit_pipeline import SystemHealthAuditPipeline


class TestSystemHealthAuditPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.pipeline = SystemHealthAuditPipeline()
        self.test_dir = tempfile.TemporaryDirectory()
        
        self.random_module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.random_incident_id = str(uuid.uuid4())
        self.random_metric_value = random.randint(100, 9999)
        
        self.incident_data = {"incident_id": self.random_incident_id, "status": "critical"}
        self.audit_summary = {"summary": f"Audit passed for {self.random_module_name}"}
        self.metrics = {"cpu_load": self.random_metric_value}
        self.dashboard_format = "json"
        self.incidents_list = [self.random_incident_id]
        self.patches_list = [f"patch_{uuid.uuid4().hex[:6]}"]
        
        self.report_path = os.path.join(self.test_dir.name, f"report_{uuid.uuid4().hex}.json")
        self.dashboard_path = os.path.join(self.test_dir.name, f"dashboard_{uuid.uuid4().hex}.json")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_run_audit_pipeline_real_integration(self):
        result = self.pipeline.run_audit_pipeline(
            module_name=self.random_module_name,
            incident_data=self.incident_data,
            audit_summary=self.audit_summary,
            metrics=self.metrics,
            dashboard_format=self.dashboard_format,
            incidents_list=self.incidents_list,
            patches_list=self.patches_list,
            report_path=self.report_path,
            dashboard_path=self.dashboard_path
        )

        self.assertIsInstance(result, dict)
        self.assertIn("telemetry", result)
        self.assertIn("aggregation", result)
        self.assertIn("notification", result)

    def test_process_audit_stream_integration(self):
        stream_content = f"telemetry_stream_data_{uuid.uuid4().hex}"
        stream = StringIO(stream_content)
        stream_path = f"/virtual/path/{uuid.uuid4().hex}.log"

        telemetry_res, aggregator_res = self.pipeline.process_audit_stream(stream, stream_path)

        self.assertIsNotNone(telemetry_res)
        self.assertIsNotNone(aggregator_res)

    def test_export_and_save_pipeline_artifacts_real_io(self):
        payload = {
            "module": self.random_module_name,
            "metric": self.random_metric_value,
            "unique_run_id": uuid.uuid4().hex
        }

        self.pipeline.export_and_save_pipeline_artifacts(
            payload=payload,
            report_path=self.report_path,
            dashboard_path=self.dashboard_path
        )

        self.assertTrue(os.path.exists(self.report_path), f"Report file was not created at {self.report_path}")
        self.assertTrue(os.path.exists(self.dashboard_path), f"Dashboard file was not created at {self.dashboard_path}")

        with open(self.report_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.random_module_name, content)


if __name__ == "__main__":
    unittest.main()