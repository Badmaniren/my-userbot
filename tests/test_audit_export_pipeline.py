import unittest
from unittest.mock import patch
import uuid
import random
import io

from skills.audit_export_pipeline import AuditExportPipeline


class TestAuditExportPipeline(unittest.TestCase):
    def test_pipeline_initialization_and_execution(self):
        rand_repo = f"/repo_{uuid.uuid4().hex}"
        rand_log = f"/log_{uuid.uuid4().hex}"
        rand_threshold = round(random.uniform(0.1, 99.9), 2)

        rand_source = f"src_{uuid.uuid4().hex}"
        rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rand_details = f"details_{uuid.uuid4().hex}"
        rand_telemetry = {uuid.uuid4().hex: random.randint(1, 100)}
        rand_metric_name = f"metric_{uuid.uuid4().hex}"
        rand_metric_val = round(random.uniform(1.0, 500.0), 2)
        rand_output = f"/out_{uuid.uuid4().hex}.json"

        with patch("skills.audit_export_pipeline.AnomalyAuditHub") as mock_audit_hub_cls, \
             patch("skills.audit_export_pipeline.DigestExporter") as mock_digest_exporter_cls:

            mock_hub_instance = mock_audit_hub_cls.return_value
            mock_exporter_instance = mock_digest_exporter_cls.return_value

            pipeline = AuditExportPipeline(
                repo_path=rand_repo,
                log_path=rand_log,
                threshold=rand_threshold
            )

            mock_audit_hub_cls.assert_called_once_with(
                repo_path=rand_repo,
                log_path=rand_log,
                threshold=rand_threshold
            )
            mock_digest_exporter_cls.assert_called_once()

            pipeline.run_audit_and_export(
                source=rand_source,
                severity=rand_severity,
                details=rand_details,
                telemetry_snapshot=rand_telemetry,
                metric_name=rand_metric_name,
                metric_value=rand_metric_val,
                output_json_path=rand_output
            )

            mock_hub_instance.log_anomaly.assert_called_once_with(
                source=rand_source,
                severity=rand_severity,
                details=rand_details,
                telemetry_snapshot=rand_telemetry
            )
            mock_hub_instance.aggregate_and_report.assert_called_once_with(
                metric_name=rand_metric_name,
                value=rand_metric_val
            )
            mock_hub_instance.generate_final_report.assert_called_once()
            mock_exporter_instance.export_json_report.assert_called_once_with(rand_output)

    def test_pipeline_stream_export(self):
        rand_repo = f"/repo_{uuid.uuid4().hex}"
        rand_log = f"/log_{uuid.uuid4().hex}"
        rand_threshold = round(random.uniform(0.1, 50.0), 2)

        rand_stream_id = f"stream_{uuid.uuid4().hex}"
        rand_output_path = f"/path/to/stream_{uuid.uuid4().hex}.json"
        rand_return_val = f"result_{uuid.uuid4().hex}"

        with patch("skills.audit_export_pipeline.AnomalyAuditHub"), \
             patch("skills.audit_export_pipeline.DigestExporter") as mock_digest_exporter_cls:

            mock_exporter_instance = mock_digest_exporter_cls.return_value
            mock_exporter_instance.export_stream_to_json.return_value = rand_return_val

            pipeline = AuditExportPipeline(
                repo_path=rand_repo,
                log_path=rand_log,
                threshold=rand_threshold
            )

            res = pipeline.export_stream(rand_stream_id, rand_output_path)

            mock_exporter_instance.export_stream_to_json.assert_called_once_with(
                rand_stream_id, rand_output_path
            )
            self.assertEqual(res, rand_return_val)

    def test_pipeline_error_propagation(self):
        rand_repo = f"/repo_{uuid.uuid4().hex}"
        rand_log = f"/log_{uuid.uuid4().hex}"
        rand_threshold = round(random.uniform(1.0, 10.0), 2)

        rand_error_msg = f"err_{uuid.uuid4().hex}"

        with patch("skills.audit_export_pipeline.AnomalyAuditHub") as mock_audit_hub_cls, \
             patch("skills.audit_export_pipeline.DigestExporter"):

            mock_hub_instance = mock_audit_hub_cls.return_value
            mock_hub_instance.generate_final_report.side_effect = RuntimeError(rand_error_msg)

            pipeline = AuditExportPipeline(
                repo_path=rand_repo,
                log_path=rand_log,
                threshold=rand_threshold
            )

            with self.assertRaises(RuntimeError) as ctx:
                pipeline.run_audit_and_export(
                    source=uuid.uuid4().hex,
                    severity="HIGH",
                    details=uuid.uuid4().hex,
                    telemetry_snapshot={},
                    metric_name=uuid.uuid4().hex,
                    metric_value=123.45,
                    output_json_path=f"/{uuid.uuid4().hex}.json"
                )

            self.assertIn(rand_error_msg, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()