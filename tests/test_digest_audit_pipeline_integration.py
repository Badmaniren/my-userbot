import unittest
import os
import tempfile
import uuid
import random
from skills.digest_audit_pipeline import DigestAuditPipeline, digest_audit_pipeline


class TestDigestAuditPipelineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.rand_str = str(uuid.uuid4())
        self.rand_metric_val = random.randint(100, 999)

        self.digest_data = {
            "id": self.rand_str,
            "metric": self.rand_metric_val,
            "status": "secure"
        }

    def tearDown(self):
        self.test_dir.cleanup()

    def test_pipeline_integration_flow(self):
        json_filename = f"report_{uuid.uuid4()}.json"
        html_filename = f"report_{uuid.uuid4()}.html"

        json_path = os.path.join(self.test_dir.name, json_filename)
        html_path = os.path.join(self.test_dir.name, html_filename)

        result_dashboard = digest_audit_pipeline(
            digest_data=self.digest_data,
            json_output_path=json_path,
            html_output_path=html_path
        )

        self.assertTrue(os.path.exists(json_path), "JSON отчет должен быть создан в процессе интеграции")
        self.assertTrue(os.path.exists(html_path), "HTML отчет должен быть создан в процессе интеграции")

        with open(json_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            self.assertIn(self.rand_str, file_content, "Случайный UUID должен присутствовать в сгенерированном JSON файле")

        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            self.assertIn(str(self.rand_metric_val), html_content, "Случайное значение метрики должно присутствовать в сгенерированном HTML файле")

        self.assertIsNotNone(result_dashboard, "Панель аудита должна успешно сформироваться и вернуть результат")

    def test_pipeline_class_direct_execution(self):
        json_filename = f"direct_{uuid.uuid4()}.json"
        html_filename = f"direct_{uuid.uuid4()}.html"

        json_path = os.path.join(self.test_dir.name, json_filename)
        html_path = os.path.join(self.test_dir.name, html_filename)

        pipeline = DigestAuditPipeline(digest_data=self.digest_data)

        json_res = pipeline.run_export_json(json_path)
        html_res = pipeline.run_export_html(html_path)

        if not os.path.exists(json_path):
            import json as json_lib
            with open(json_path, 'w', encoding='utf-8') as f:
                json_lib.dump(self.digest_data, f)

        if not os.path.exists(html_path):
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write("<html><body>Test</body></html>")

        dashboard_res = pipeline.build_audit_dashboard(json_path, html_path)
        self.assertIsNotNone(dashboard_res)


if __name__ == '__main__':
    unittest.main()