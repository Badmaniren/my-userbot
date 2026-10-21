import unittest
import os
import tempfile
import uuid
import random
from skills.digest_audit_pipeline import DigestAuditPipeline, DigestAuditPipelineError


class TestDigestAuditPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.test_dir.cleanup)

        self.source_id = f"service_{uuid.uuid4().hex[:8]}"
        self.severity_level = random.choice(["INFO", "WARNING", "CRITICAL", "ERROR"])
        self.metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        self.metric_val = round(random.uniform(10.0, 500.0), 2)
        self.details_msg = f"Test anomaly detail uuid: {uuid.uuid4()}"

    def test_pipeline_audit_and_export_json_integration(self):
        json_filename = f"report_{uuid.uuid4().hex}.json"
        output_path = os.path.join(self.test_dir.name, json_filename)

        pipeline = DigestAuditPipeline(repo_path=None, log_path=None, threshold=None)

        log_res = pipeline.log_anomaly(
            source=self.source_id,
            severity=self.severity_level,
            details=self.details_msg
        )
        self.assertIsNotNone(log_res)

        agg_res = pipeline.aggregate_and_report(self.metric_name, self.metric_val)
        self.assertIsNotNone(agg_res)

        exported_path = pipeline.run_audit_and_export_json(output_path)

        self.assertTrue(os.path.exists(exported_path), f"Файл отчета не был создан по пути: {exported_path}")
        self.assertTrue(os.path.getsize(exported_path) > 0, "Экспортированный JSON файл пуст.")

    def test_pipeline_audit_and_export_html_integration(self):
        html_filename = f"report_{uuid.uuid4().hex}.html"
        output_path = os.path.join(self.test_dir.name, html_filename)

        pipeline = DigestAuditPipeline(repo_path=None, log_path=None, threshold=None)

        pipeline.log_anomaly(
            source=self.source_id,
            severity=self.severity_level,
            details=self.details_msg
        )
        pipeline.aggregate_and_report(self.metric_name, self.metric_val)

        exported_path = pipeline.run_audit_and_export_html(output_path)

        self.assertTrue(os.path.exists(exported_path), f"Файл HTML отчета не был создан: {exported_path}")
        self.assertTrue(os.path.getsize(exported_path) > 0, "Экспортированный HTML файл пуст.")

    def test_pipeline_run_audit_and_export_dynamic_extension(self):
        ext = random.choice([".json", ".html"])
        filename = f"dynamic_report_{uuid.uuid4().hex}{ext}"
        output_path = os.path.join(self.test_dir.name, filename)

        pipeline = DigestAuditPipeline()

        pipeline.log_anomaly(
            source=self.source_id,
            severity=self.severity_level,
            details=self.details_msg
        )

        exported_path = pipeline.run_audit_and_export(output_path)

        self.assertTrue(os.path.exists(exported_path))
        self.assertTrue(exported_path.endswith(ext))
        self.assertTrue(os.path.getsize(exported_path) > 0)


if __name__ == "__main__":
    unittest.main()