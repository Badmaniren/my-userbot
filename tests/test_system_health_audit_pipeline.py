import unittest
from unittest.mock import MagicMock, patch
import io
import random
import uuid
import string

from skills.system_health_audit_pipeline import SystemHealthAuditPipeline


class TestSystemHealthAuditPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = SystemHealthAuditPipeline()

    def test_run_audit_pipeline_success(self):
        module_name = f"mod_{uuid.uuid4().hex[:8]}"
        incident_data = {uuid.uuid4().hex: random.randint(1, 100)}
        audit_summary = f"summary_{uuid.uuid4().hex[:8]}"
        metrics = {uuid.uuid4().hex: random.random()}
        dashboard_format = random.choice(["json", "yaml", "html"])
        incidents_list = [uuid.uuid4().hex, uuid.uuid4().hex]
        patches_list = [uuid.uuid4().hex]
        report_path = f"/path/to/{uuid.uuid4().hex}.rpt"
        dashboard_path = f"/path/to/{uuid.uuid4().hex}.dash"

        expected_telemetry = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_aggregation = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(self.pipeline.telemetry_collector, "collect_and_process_telemetry", return_value=expected_telemetry) as mock_telemetry, \
             patch.object(self.pipeline.aggregator, "collect_and_aggregate", return_value=expected_aggregation) as mock_aggregator:

            result = self.pipeline.run_audit_pipeline(
                module_name,
                incident_data,
                audit_summary,
                metrics,
                dashboard_format,
                incidents_list,
                patches_list,
                report_path,
                dashboard_path
            )

            mock_telemetry.assert_called_once_with(
                module_name,
                incident_data,
                audit_summary,
                metrics,
                dashboard_format,
                incidents_list,
                patches_list,
                report_path,
                dashboard_path
            )

            mock_aggregator.assert_called_once_with(
                module_name,
                incident_data,
                audit_summary,
                metrics,
                dashboard_format,
                incidents_list,
                patches_list
            )

            self.assertEqual(result["telemetry"], expected_telemetry)
            self.assertEqual(result["aggregation"], expected_aggregation)

    def test_process_audit_stream(self):
        random_bytes = ''.join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        stream = io.BytesIO(random_bytes)
        stream_path = f"/streams/{uuid.uuid4().hex}.stream"

        expected_telemetry_res = {uuid.uuid4().hex: random.randint(10, 50)}
        expected_aggregator_res = {uuid.uuid4().hex: random.randint(51, 100)}

        with patch.object(self.pipeline.telemetry_collector, "process_telemetry_stream", return_value=expected_telemetry_res) as mock_t_stream, \
             patch.object(self.pipeline.aggregator, "process_stream", return_value=expected_aggregator_res) as mock_a_stream:

            telemetry_res, aggregator_res = self.pipeline.process_audit_stream(stream, stream_path)

            mock_t_stream.assert_called_once_with(stream, stream_path)
            mock_a_stream.assert_called_once()
            
            self.assertEqual(telemetry_res, expected_telemetry_res)
            self.assertEqual(aggregator_res, expected_aggregator_res)
            self.assertEqual(stream.tell(), 0)

    def test_export_and_save_pipeline_artifacts(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex, uuid.uuid4().hex: random.randint(1, 1000)}
        report_path = f"/exports/{uuid.uuid4().hex}.json"
        dashboard_path = f"/dashboards/{uuid.uuid4().hex}.yaml"

        with patch.object(self.pipeline.telemetry_collector, "export_comprehensive_report") as mock_export, \
             patch.object(self.pipeline.aggregator, "save_dashboard_file") as mock_save:

            self.pipeline.export_and_save_pipeline_artifacts(payload, report_path, dashboard_path)

            mock_export.assert_called_once_with(payload, report_path)
            mock_save.assert_called_once_with(payload, dashboard_path)


if __name__ == "__main__":
    unittest.main()