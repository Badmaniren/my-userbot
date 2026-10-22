import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.audit_export_pipeline import AuditExportPipeline, AuditExportPipelineError
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.digest_exporter import DigestExporter


class TestAuditExportPipeline(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/repo/{uuid.uuid4().hex}"
        self.rand_log = f"/var/log/{uuid.uuid4().hex}.log"
        self.rand_threshold = random.uniform(0.1, 99.9)
        self.rand_output = f"/tmp/{uuid.uuid4().hex}.json"

    @patch('skills.audit_export_pipeline.DigestExporter')
    @patch('skills.audit_export_pipeline.omaly_audit_hub' if False else 'skills.audit_export_pipeline.AnomalyAuditHub')
    def test_pipeline_initialization(self, mock_hub_cls, mock_exporter_cls):
        hub_instance = mock_hub_cls.return_value
        exporter_instance = mock_exporter_cls.return_value

        pipeline = AuditExportPipeline(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )

        mock_hub_cls.assert_called_once_with(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold
        )
        mock_exporter_cls.assert_called_once()
        self.assertIsNotNone(pipeline)

    def test_run_export_pipeline_json_success(self):
        rand_source = uuid.uuid4().hex
        rand_severity = random.choice(["INFO", "WARN", "CRITICAL"])
        rand_details = uuid.uuid4().hex
        rand_metric = uuid.uuid4().hex
        rand_val = random.uniform(1.0, 1000.0)
        rand_out_path = f"/export/{uuid.uuid4().hex}.json"
        rand_result_str = uuid.uuid4().hex

        with patch('skills.audit_export_pipeline.AnomalyAuditHub') as mock_hub_cls, \
             patch('skills.audit_export_pipeline.DigestExporter') as mock_exporter_cls:

            mock_hub = mock_hub_cls.return_value
            mock_exporter = mock_exporter_cls.return_value
            mock_exporter.export_to_json.return_value = rand_result_str

            pipeline = AuditExportPipeline(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.rand_threshold
            )

            res = pipeline.run_pipeline_and_export(
                metric_name=rand_metric,
                value=rand_val,
                output_path=rand_out_path,
                export_format="json"
            )

            mock_hub.aggregate_and_report.assert_called_once_with(rand_metric, rand_val)
            mock_hub.generate_final_report.assert_called_once()
            mock_exporter.export_to_json.assert_called_once_with(rand_out_path)
            self.assertEqual(res, rand_result_str)

    def test_run_export_pipeline_html_success(self):
        rand_metric = uuid.uuid4().hex
        rand_val = random.uniform(1.0, 1000.0)
        rand_out_path = f"/export/{uuid.uuid4().hex}.html"
        rand_result_str = uuid.uuid4().hex

        with patch('skills.audit_export_pipeline.AnomalyAuditHub') as mock_hub_cls, \
             patch('skills.audit_export_pipeline.DigestExporter') as mock_exporter_cls:

            mock_hub = mock_hub_cls.return_value
            mock_exporter = mock_exporter_cls.return_value
            mock_exporter.export_to_html.return_value = rand_result_str

            pipeline = AuditExportPipeline(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.rand_threshold
            )

            res = pipeline.run_pipeline_and_export(
                metric_name=rand_metric,
                value=rand_val,
                output_path=rand_out_path,
                export_format="html"
            )

            mock_exporter.export_to_html.assert_called_once_with(rand_out_path)
            self.assertEqual(res, rand_result_str)

    def test_run_export_pipeline_invalid_format(self):
        rand_metric = uuid.uuid4().hex
        rand_val = random.uniform(1.0, 1000.0)
        rand_out_path = f"/export/{uuid.uuid4().hex}.unknown"
        rand_bad_format = ''.join(random.choices(string.ascii_lowercase, k=6))

        with patch('skills.audit_export_pipeline.AnomalyAuditHub'), \
             patch('skills.audit_export_pipeline.DigestExporter'):

            pipeline = AuditExportPipeline(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.rand_threshold
            )

            with self.assertRaises(AuditExportPipelineError):
                pipeline.run_pipeline_and_export(
                    metric_name=rand_metric,
                    value=rand_val,
                    output_path=rand_out_path,
                    export_format=rand_bad_format
                )

    def test_pipeline_catches_hub_exception(self):
        rand_metric = uuid.uuid4().hex
        rand_val = random.uniform(1.0, 1000.0)
        rand_out_path = f"/export/{uuid.uuid4().hex}.json"

        with patch('skills.audit_export_pipeline.AnomalyAuditHub') as mock_hub_cls, \
             patch('skills.audit_export_pipeline.DigestExporter'):

            mock_hub = mock_hub_cls.return_value
            mock_hub.aggregate_and_report.side_effect = Exception(uuid.uuid4().hex)

            pipeline = AuditExportPipeline(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.rand_threshold
            )

            with self.assertRaises(AuditExportPipelineError):
                pipeline.run_pipeline_and_export(
                    metric_name=rand_metric,
                    value=rand_val,
                    output_path=rand_out_path,
                    export_format="json"
                )

    def test_pipeline_catches_exporter_exception(self):
        rand_metric = uuid.uuid4().hex
        rand_val = random.uniform(1.0, 1000.0)
        rand_out_path = f"/export/{uuid.uuid4().hex}.json"

        with patch('skills.audit_export_pipeline.AnomalyAuditHub'), \
             patch('skills.audit_export_pipeline.DigestExporter') as mock_exporter_cls:

            mock_exporter = mock_exporter_cls.return_value
            mock_exporter.export_to_json.side_effect = Exception(uuid.uuid4().hex)

            pipeline = AuditExportPipeline(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.rand_threshold
            )

            with self.assertRaises(AuditExportPipelineError):
                pipeline.run_pipeline_and_export(
                    metric_name=rand_metric,
                    value=rand_val,
                    output_path=rand_out_path,
                    export_format="json"
                )

    def test_log_and_export_anomaly(self):
        rand_source = uuid.uuid4().hex
        rand_severity = uuid.uuid4().hex
        rand_details = {"info": uuid.uuid4().hex}
        rand_snapshot = {"cpu": random.randint(1, 100)}
        rand_out_path = f"/export/{uuid.uuid4().hex}.json"
        rand_res = uuid.uuid4().hex

        with patch('skills.audit_export_pipeline.AnomalyAuditHub') as mock_hub_cls, \
             patch('skills.audit_export_pipeline.DigestExporter') as mock_exporter_cls:

            mock_hub = mock_hub_cls.return_value
            mock_exporter = mock_exporter_cls.return_value
            mock_exporter.export_json_report.return_value = rand_res

            pipeline = AuditExportPipeline(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.rand_threshold
            )

            res = pipeline.record_anomaly_and_export_report(
                source=rand_source,
                severity=rand_severity,
                details=rand_details,
                telemetry_snapshot=rand_snapshot,
                output_path=rand_out_path
            )

            mock_hub.log_anomaly.assert_called_once_with(
                source=rand_source,
                severity=rand_severity,
                details=rand_details,
                telemetry_snapshot=rand_snapshot
            )
            mock_exporter.export_json_report.assert_called_once_with(rand_out_path)
            self.assertEqual(res, rand_res)


if __name__ == '__main__':
    unittest.main()