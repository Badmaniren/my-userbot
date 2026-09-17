import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

from skills.telemetry_health_pipeline import (
    TelemetryHealthPipeline,
    PipelineCompositionError
)

class TestTelemetryHealthPipeline(unittest.TestCase):
    def setUp(self):
        self.stream_id = uuid.uuid4().hex
        self.endpoint = f"http://{uuid.uuid4().hex}.local/{uuid.uuid4().hex}"
        self.buffer_size = random.randint(1024, 65536)
        self.pipeline = TelemetryHealthPipeline(
            stream_id=self.stream_id,
            endpoint=self.endpoint,
            buffer_size=self.buffer_size
        )

    def test_pipeline_initialization_success(self):
        self.assertEqual(self.pipeline.streamer.stream_id, self.stream_id)
        self.assertEqual(self.pipeline.streamer.endpoint, self.endpoint)
        self.assertEqual(self.pipeline.streamer.buffer_size, self.buffer_size)
        self.assertIsNotNone(self.pipeline.processor)
        self.assertIsNotNone(self.pipeline.collector)

    def test_run_pipeline_cycle_success(self):
        random_source_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        random_raw_packet = {uuid.uuid4().hex: uuid.uuid4().hex}
        random_module_name = uuid.uuid4().hex
        random_incident_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        random_audit_summary = uuid.uuid4().hex
        random_metrics = {uuid.uuid4().hex: random.random()}
        random_dashboard_format = uuid.uuid4().hex
        random_incidents_list = [uuid.uuid4().hex]
        random_patches_list = [uuid.uuid4().hex]
        random_report_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.rpt"
        random_dashboard_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.dash"

        with patch.object(self.pipeline.streamer, 'read_from_source', return_value=random_raw_packet) as mock_read, \
             patch.object(self.pipeline.processor, 'process_packet', return_value=random_raw_packet) as mock_process, \
             patch.object(self.pipeline.collector, 'collect_and_process_telemetry') as mock_collect:

            result = self.pipeline.run_pipeline_cycle(
                source_path=random_source_path,
                module_name=random_module_name,
                incident_data=random_incident_data,
                audit_summary=random_audit_summary,
                metrics=random_metrics,
                dashboard_format=random_dashboard_format,
                incidents_list=random_incidents_list,
                patches_list=random_patches_list,
                report_path=random_report_path,
                dashboard_path=random_dashboard_path
            )

            mock_read.assert_called_once_with(random_source_path)
            mock_process.assert_called_once_with(random_raw_packet)
            mock_collect.assert_called_once_with(
                module_name=random_module_name,
                incident_data=random_incident_data,
                audit_summary=random_audit_summary,
                metrics=random_metrics,
                dashboard_format=random_dashboard_format,
                incidents_list=random_incidents_list,
                patches_list=random_patches_list,
                report_path=random_report_path,
                dashboard_path=random_dashboard_path
            )
            self.assertEqual(result, mock_collect.return_value)

    def test_run_pipeline_cycle_streamer_error_propagation(self):
        random_source_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        error_message = uuid.uuid4().hex

        with patch.object(self.pipeline.streamer, 'read_from_source', side_effect=Exception(error_message)) as mock_read:
            with self.assertRaises(Exception) as ctx:
                self.pipeline.run_pipeline_cycle(
                    source_path=random_source_path,
                    module_name=uuid.uuid4().hex,
                    incident_data={},
                    audit_summary=uuid.uuid4().hex,
                    metrics={},
                    dashboard_format=uuid.uuid4().hex,
                    incidents_list=[],
                    patches_list=[],
                    report_path=f"/{uuid.uuid4().hex}.rpt",
                    dashboard_path=f"/{uuid.uuid4().hex}.dash"
                )
            self.assertIn(error_message, str(ctx.exception))
            mock_read.assert_called_once_with(random_source_path)

    def test_run_pipeline_cycle_processor_error_propagation(self):
        random_source_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        random_raw_packet = {uuid.uuid4().hex: uuid.uuid4().hex}
        error_message = uuid.uuid4().hex

        with patch.object(self.pipeline.streamer, 'read_from_source', return_value=random_raw_packet), \
             patch.object(self.pipeline.processor, 'process_packet', side_effect=ValueError(error_message)):
            with self.assertRaises(ValueError) as ctx:
                self.pipeline.run_pipeline_cycle(
                    source_path=random_source_path,
                    module_name=uuid.uuid4().hex,
                    incident_data={},
                    audit_summary=uuid.uuid4().hex,
                    metrics={},
                    dashboard_format=uuid.uuid4().hex,
                    incidents_list=[],
                    patches_list=[],
                    report_path=f"/{uuid.uuid4().hex}.rpt",
                    dashboard_path=f"/{uuid.uuid4().hex}.dash"
                )
            self.assertIn(error_message, str(ctx.exception))

    def test_run_pipeline_cycle_collector_error_propagation(self):
        random_source_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        random_raw_packet = {uuid.uuid4().hex: uuid.uuid4().hex}
        error_message = uuid.uuid4().hex

        with patch.object(self.pipeline.streamer, 'read_from_source', return_value=random_raw_packet), \
             patch.object(self.pipeline.processor, 'process_packet', return_value=random_raw_packet), \
             patch.object(self.pipeline.collector, 'collect_and_process_telemetry', side_effect=RuntimeError(error_message)):
            with self.assertRaises(RuntimeError) as ctx:
                self.pipeline.run_pipeline_cycle(
                    source_path=random_source_path,
                    module_name=uuid.uuid4().hex,
                    incident_data={},
                    audit_summary=uuid.uuid4().hex,
                    metrics={},
                    dashboard_format=uuid.uuid4().hex,
                    incidents_list=[],
                    patches_list=[],
                    report_path=f"/{uuid.uuid4().hex}.rpt",
                    dashboard_path=f"/{uuid.uuid4().hex}.dash"
                )
            self.assertIn(error_message, str(ctx.exception))

    def test_stream_and_process_bytes_io(self):
        random_payload_bytes = uuid.uuid4().hex.encode('utf-8')
        random_stream = io.BytesIO(random_payload_bytes)
        random_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.log"
        processed_result_id = uuid.uuid4().hex

        with patch.object(self.pipeline.collector, 'process_telemetry_stream', return_value=processed_result_id) as mock_stream_proc:
            res = self.pipeline.stream_and_process(random_stream, random_path)
            mock_stream_proc.assert_called_once_with(random_stream, random_path)
            self.assertEqual(res, processed_result_id)

    def test_export_pipeline_report(self):
        random_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        random_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"

        with patch.object(self.pipeline.collector, 'export_comprehensive_report') as mock_export:
            self.pipeline.export_pipeline_report(random_payload, random_path)
            mock_export.assert_called_once_with(random_payload, random_path)

if __name__ == '__main__':
    unittest.main()