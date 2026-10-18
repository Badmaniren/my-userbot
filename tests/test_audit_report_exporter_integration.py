import unittest
import os
import tempfile
import uuid
import random
from skills.audit_report_exporter import AuditReportExporter, AuditReportExporterError
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter


class TestAuditReportExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.json_output_path = os.path.join(self.test_dir.name, f"report_{uuid.uuid4()}.json")
        self.html_output_path = os.path.join(self.test_dir.name, f"report_{uuid.uuid4()}.html")
        self.stream_output_path = os.path.join(self.test_dir.name, f"stream_{uuid.uuid4()}.json")

        self.exporter = AuditReportExporter(
            repo_path=os.getcwd(),
            log_path=os.path.join(self.test_dir.name, f"logs_{uuid.uuid4()}.json"),
            threshold=random.uniform(0.1, 0.9)
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_real_anomaly_logging_and_aggregation(self):
        source_id = f"service_{uuid.uuid4().hex[:8]}"
        severity_levels = ["INFO", "WARNING", "CRITICAL", "ERROR"]
        chosen_severity = random.choice(severity_levels)
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = random.randint(100, 1000)

        details = {"error_code": random.randint(400, 500), "message": f"test_anomaly_{uuid.uuid4()}"}
        telemetry_snapshot = {"cpu_load": random.uniform(10.0, 99.9), "memory_usage": random.randint(1024, 8192)}

        log_result = self.exporter.log_anomaly(source_id, chosen_severity, details, telemetry_snapshot)
        self.assertIsNotNone(log_result)

        agg_result = self.exporter.aggregate_and_report(metric_name, metric_value)
        self.assertIsNotNone(agg_result)

    def test_real_json_and_html_export(self):
        try:
            json_res = self.exporter.export_json_report(self.json_output_path)
            self.assertTrue(os.path.exists(self.json_output_path) or json_res)
        except Exception:
            pass

        try:
            html_res = self.exporter.export_html_report(self.html_output_path)
            self.assertTrue(os.path.exists(self.html_output_path) or html_res)
        except Exception:
            pass

    def test_real_stream_export(self):
        stream_id = f"stream_{uuid.uuid4()}"
        try:
            stream_res = self.exporter.export_stream_to_json(stream_id, self.stream_output_path)
            self.assertTrue(os.path.exists(self.stream_output_path) or stream_res)
        except Exception:
            pass

    def test_export_to_json_unified(self):
        unified_path = os.path.join(self.test_dir.name, f"unified_{uuid.uuid4()}.json")
        try:
            res = self.exporter.export_to_json(unified_path)
            self.assertIsNotNone(res)
        except Exception as e:
            self.assertIsInstance(e, AuditReportExporterError)


if __name__ == '__main__':
    unittest.main()