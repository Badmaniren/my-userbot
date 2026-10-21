import unittest
import os
import uuid
import random
import tempfile
from skills.digest_audit_pipeline import DigestAuditPipeline, DigestAuditPipelineError

class TestDigestAuditPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.test_dir.name, f"report_{uuid.uuid4()}.json")
        self.html_path = os.path.join(self.test_dir.name, f"report_{uuid.uuid4()}.html")

        self.pipeline = DigestAuditPipeline(
            repo_path=None,
            log_path=None,
            threshold=random.uniform(0.1, 0.9),
            output_json_path=self.json_path,
            output_html_path=self.html_path
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_run_audit_and_export_json_integration(self):
        unique_source = f"source_{uuid.uuid4()}"
        unique_details = f"details_{uuid.uuid4()}"
        severities = ["INFO", "WARNING", "CRITICAL", "ERROR"]
        selected_severity = random.choice(severities)

        metric_name = f"metric_{uuid.uuid4()}"
        metric_value = random.randint(1, 1000)

        result_path = self.pipeline.run_audit_and_export_json(
            source=unique_source,
            severity=selected_severity,
            details=unique_details,
            metric_name=metric_name,
            metric_value=metric_value
        )

        self.assertTrue(os.path.exists(result_path))
        self.assertEqual(os.path.abspath(result_path), os.path.abspath(self.json_path))

        with open(result_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(unique_source, content)
            self.assertIn(unique_details, content)
            self.assertIn(selected_severity, content)

    def test_run_audit_and_export_html_integration(self):
        unique_source = f"source_html_{uuid.uuid4()}"
        unique_details = f"details_html_{uuid.uuid4()}"
        selected_severity = random.choice(["INFO", "WARNING", "CRITICAL"])

        metric_name = f"metric_html_{uuid.uuid4()}"
        metric_value = round(random.uniform(10.0, 999.9), 2)

        result_path = self.pipeline.run_audit_and_export_html(
            source=unique_source,
            severity=selected_severity,
            details=unique_details,
            metric_name=metric_name,
            metric_value=metric_value
        )

        self.assertTrue(os.path.exists(result_path))
        self.assertEqual(os.path.abspath(result_path), os.path.abspath(self.html_path))

        with open(result_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(unique_source, content)
            self.assertIn(unique_details, content)

    def test_run_export_pipeline_integration(self):
        unique_source = f"batch_source_{uuid.uuid4()}"
        unique_details = f"batch_details_{uuid.uuid4()}"

        self.pipeline.run_audit_and_export_json(
            source=unique_source,
            severity="WARNING",
            details=unique_details
        )

        json_res, html_res = self.pipeline.run_export_pipeline()

        self.assertTrue(os.path.exists(json_res))
        self.assertTrue(os.path.exists(html_res))

        with open(json_res, "r", encoding="utf-8") as f:
            self.assertIn(unique_source, f.read())

        with open(html_res, "r", encoding="utf-8") as f:
            self.assertIn(unique_details, f.read())

if __name__ == "__main__":
    unittest.main()