import io
import os
import random
import uuid
import unittest
from unittest.mock import patch, MagicMock

from skills.telemetry_health_pipeline import (
    TelemetryHealthPipeline,
    TelemetryHealthPipelineException,
)


class TestTelemetryHealthPipelineArchitect(unittest.TestCase):
    def setUp(self) -> None:
        self.random_bytes = uuid.uuid4().bytes + os.urandom(32)
        self.pipeline = TelemetryHealthPipeline()
        self.module_name = f"mod_{uuid.uuid4().hex[:8]}"
        self.output_path = f"/tmp/{uuid.uuid4().hex}.bin"
        self.report_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.dashboard_path = f"/tmp/{uuid.uuid4().hex}.html"
        self.incident_data = {uuid.uuid4().hex: random.randint(1, 100)}
        self.audit_summary = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.metrics = {uuid.uuid4().hex: random.uniform(0.1, 99.9)}
        self.dashboard_format = uuid.uuid4().hex[:5]
        self.incidents_list = [uuid.uuid4().hex, uuid.uuid4().hex]
        self.patches_list = [uuid.uuid4().hex]

    def test_pipeline_initialization_and_composition(self) -> None:
        self.assertIsNotNone(self.pipeline.processor)
        self.assertIsNotNone(self.pipeline.collector)
        self.assertEqual(self.pipeline.processor, self.pipeline.telemetry_processor)

    def test_comprehensive_pipeline_execution(self) -> None:
        expected_result = {uuid.uuid4().hex: uuid.uuid4().hex}
        with patch.object(
            self.pipeline.collector,
            "collect_and_process_telemetry",
            return_value=expected_result
        ) as mock_collect:
            res = self.pipeline.run_full_pipeline(
                self.module_name,
                self.incident_data,
                self.audit_summary,
                self.metrics,
                self.dashboard_format,
                self.incidents_list,
                self.patches_list,
                self.report_path,
                self.dashboard_path
            )
            self.assertEqual(res, expected_result)
            mock_collect.assert_called_once_with(
                self.module_name,
                self.incident_data,
                self.audit_summary,
                self.metrics,
                self.dashboard_format,
                self.incidents_list,
                self.patches_list,
                self.report_path,
                self.dashboard_path
            )

    def test_export_pipeline_report_delegation(self) -> None:
        payload = {uuid.uuid4().hex: random.randint(100, 999)}
        with patch.object(
            self.pipeline.collector,
            "export_comprehensive_report"
        ) as mock_export:
            self.pipeline.export_report(payload, self.output_path)
            mock_export.assert_called_once_with(payload, self.output_path)

    def test_process_binary_stream_valid(self) -> None:
        stream = io.BytesIO(self.random_bytes)
        expected_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        with patch.object(
            self.pipeline.collector,
            "process_telemetry_stream",
            return_value=expected_dict
        ) as mock_stream:
            res = self.pipeline.execute_stream_pipeline(stream, self.output_path)
            self.assertEqual(res, expected_dict)
            mock_stream.assert_called_once_with(stream, self.output_path)

    def test_process_binary_stream_invalid_type_raises(self) -> None:
        invalid_stream = uuid.uuid4().hex
        with self.assertRaises(TelemetryHealthPipelineException):
            self.pipeline.execute_stream_pipeline(invalid_stream, self.output_path)

    def test_pipeline_error_propagation_strict_typing(self) -> None:
        random_error_msg = uuid.uuid4().hex
        with patch.object(
            self.pipeline.collector,
            "collect_and_process_telemetry",
            side_effect=Exception(random_error_msg)
        ):
            with self.assertRaises(TelemetryHealthPipelineException) as ctx:
                self.pipeline.run_full_pipeline(
                    self.module_name,
                    self.incident_data,
                    self.audit_summary,
                    self.metrics,
                    self.dashboard_format,
                    self.incidents_list,
                    self.patches_list,
                    self.report_path,
                    self.dashboard_path
                )
            self.assertIn(random_error_msg, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()