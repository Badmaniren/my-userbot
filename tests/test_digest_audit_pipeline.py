import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import json
import io

from skills.digest_audit_pipeline import DigestAuditPipeline, digest_audit_pipeline
from skills.digest_dashboard_builder import DigestDashboardBuilderError
from skills.digest_exporter import DigestExporterError


class TestDigestAuditPipeline(unittest.TestCase):

    def setUp(self):
        self.random_prefix = uuid.uuid4().hex[:8]
        self.digest_data = {
            "id": self.random_prefix,
            "metric": random.randint(100, 999),
            "status": "SECURE"
        }
        self.json_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.html_path = f"/tmp/{uuid.uuid4().hex}.html"
        self.anomaly_visualizer = MagicMock()
        self.stability_digest = MagicMock()

    def tearDown(self):
        for path in [self.json_path, self.html_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_pipeline_initialization(self):
        pipeline = DigestAuditPipeline(
            digest_data=self.digest_data,
            anomaly_visualizer=self.anomaly_visualizer,
            stability_digest=self.stability_digest
        )
        self.assertEqual(pipeline.digest_data, self.digest_data)
        self.assertEqual(pipeline.anomaly_visualizer, self.anomaly_visualizer)
        self.assertEqual(pipeline.stability_digest, self.stability_digest)
        self.assertIsNotNone(pipeline.builder)
        self.assertIsNotNone(pipeline.exporter)

    def test_run_export_json_fallback_and_methods(self):
        pipeline = DigestAuditPipeline(digest_data=self.digest_data)

        with patch.object(pipeline.exporter, 'export_json_report', create=True, side_effect=AttributeError):
            with patch.object(pipeline.exporter, 'export_to_json') as mock_export_to_json:
                mock_export_to_json.return_value = self.json_path
                res = pipeline.run_export_json(self.json_path)
                self.assertEqual(res, self.json_path)
                mock_export_to_json.assert_called_once_with(self.digest_data, self.json_path)

        with patch.object(pipeline.exporter, 'export_json_report', create=True) as mock_report:
            mock_report.return_value = self.json_path
            res = pipeline.run_export_json(self.json_path)
            self.assertEqual(res, self.json_path)
            mock_report.assert_called_once_with(self.json_path)

    def test_run_export_html_fallback_and_methods(self):
        pipeline = DigestAuditPipeline(digest_data=self.digest_data)

        with patch.object(pipeline.exporter, 'export_html_report', create=True, side_effect=AttributeError):
            with patch.object(pipeline.exporter, 'export_to_html') as mock_export_to_html:
                mock_export_to_html.return_value = self.html_path
                res = pipeline.run_export_html(self.html_path)
                self.assertEqual(res, self.html_path)
                mock_export_to_html.assert_called_once_with(self.digest_data, self.html_path)

        with patch.object(pipeline.exporter, 'export_html_report', create=True) as mock_report:
            mock_report.return_value = self.html_path
            res = pipeline.run_export_html(self.html_path)
            self.assertEqual(res, self.html_path)
            mock_report.assert_called_once_with(self.html_path)

    def test_build_audit_dashboard(self):
        pipeline = DigestAuditPipeline(digest_data=self.digest_data)
        expected_dashboard_output = f"/tmp/{uuid.uuid4().hex}.dashboard"

        with patch.object(pipeline.builder, 'build_dashboard') as mock_build:
            mock_build.return_value = expected_dashboard_output
            res = pipeline.build_audit_dashboard(self.json_path, self.html_path)
            self.assertEqual(res, expected_dashboard_output)
            mock_build.assert_called_once_with(self.json_path, self.html_path)

    def test_digest_audit_pipeline_function_integration(self):
        pipeline_mock = MagicMock()
        expected_res = f"dashboard_{uuid.uuid4().hex}"
        pipeline_mock.run_export_json.return_value = self.json_path
        pipeline_mock.run_export_html.return_value = self.html_path
        pipeline_mock.build_audit_dashboard.return_value = expected_res

        with patch('skills.digest_audit_pipeline.DigestAuditPipeline', return_value=pipeline_mock) as MockPipeline:
            res = digest_audit_pipeline(
                digest_data=self.digest_data,
                json_output_path=self.json_path,
                html_output_path=self.html_path,
                anomaly_visualizer=self.anomaly_visualizer,
                stability_digest=self.stability_digest
            )

            MockPipeline.assert_called_once_with(
                digest_data=self.digest_data,
                anomaly_visualizer=self.anomaly_visualizer,
                stability_digest=self.stability_digest
            )
            pipeline_mock.run_export_json.assert_called_once_with(self.json_path)
            pipeline_mock.run_export_html.assert_called_once_with(self.html_path)
            pipeline_mock.build_audit_dashboard.assert_called_once_with(self.json_path, self.html_path)
            self.assertEqual(res, expected_res)

            self.assertTrue(os.path.exists(self.json_path))
            self.assertTrue(os.path.exists(self.html_path))

            with open(self.json_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
                self.assertEqual(loaded_data, self.digest_data)

    def test_digest_audit_pipeline_files_already_exist(self):
        pipeline_mock = MagicMock()
        expected_res = f"dashboard_{uuid.uuid4().hex}"
        pipeline_mock.run_export_json.return_value = self.json_path
        pipeline_mock.run_export_html.return_value = self.html_path
        pipeline_mock.build_audit_dashboard.return_value = expected_res

        custom_json_content = {"pre-existing": uuid.uuid4().hex}
        custom_html_content = f"<div>{uuid.uuid4().hex}</div>"

        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(custom_json_content, f)
        with open(self.html_path, 'w', encoding='utf-8') as f:
            f.write(custom_html_content)

        with patch('skills.digest_audit_pipeline.DigestAuditPipeline', return_value=pipeline_mock):
            digest_audit_pipeline(
                digest_data=self.digest_data,
                json_output_path=self.json_path,
                html_output_path=self.html_path
            )

        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.assertEqual(json.load(f), custom_json_content)

        with open(self.html_path, 'r', encoding='utf-8') as f:
            self.assertEqual(f.read(), custom_html_content)


if __name__ == '__main__':
    unittest.main()