import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.system_health_audit_pipeline import SystemHealthAuditPipeline


class TestSystemHealthAuditPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = SystemHealthAuditPipeline()
        self.module_name = f"mod_{uuid.uuid4().hex[:8]}"
        self.incident_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.audit_summary = uuid.uuid4().hex
        self.metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        self.dashboard_format = uuid.uuid4().hex
        self.incidents_list = [uuid.uuid4().hex]
        self.patches_list = [uuid.uuid4().hex]
        self.report_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.dashboard_path = f"/tmp/{uuid.uuid4().hex}.html"

    def test_run_audit_pipeline_success(self):
        telemetry_val = {uuid.uuid4().hex: uuid.uuid4().hex}
        aggregate_val = {uuid.uuid4().hex: uuid.uuid4().hex}
        notification_val = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.system_health_telemetry_collector.SystemHealthTelemetryCollector.collect_and_process_telemetry", return_value=telemetry_val) as mock_telemetry, \
             patch("skills.system_health_aggregator.SystemHealthAggregator.collect_and_aggregate", return_value=aggregate_val) as mock_aggregator, \
             patch("skills.notification_channel_dispatcher.NotificationChannelDispatcher.dispatch_critical_alert", return_value=notification_val, create=True) as mock_notifier:

            result = self.pipeline.run_audit_pipeline(
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

            mock_telemetry.assert_called_once_with(
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
            mock_aggregator.assert_called_once_with(
                self.module_name,
                self.incident_data,
                self.audit_summary,
                self.metrics,
                self.dashboard_format,
                self.incidents_list,
                self.patches_list
            )
            mock_notifier.assert_called_once_with(
                self.module_name,
                self.incident_data,
                self.audit_summary,
                self.metrics,
                self.incidents_list
            )

            self.assertEqual(result["telemetry"], telemetry_val)
            self.assertEqual(result["aggregation"], aggregate_val)
            self.assertEqual(result["notification"], notification_val)

    def test_process_audit_stream(self):
        stream_content = uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(stream_content)
        stream_path = f"/tmp/{uuid.uuid4().hex}.log"

        telemetry_res_val = {uuid.uuid4().hex: uuid.uuid4().hex}
        aggregator_res_val = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.system_health_telemetry_collector.SystemHealthTelemetryCollector.process_telemetry_stream", return_value=telemetry_res_val) as mock_telemetry_stream, \
             patch("skills.system_health_aggregator.SystemHealthAggregator.process_stream", return_value=aggregator_res_val) as mock_aggregator_stream:

            t_res, a_res = self.pipeline.process_audit_stream(stream, stream_path)

            mock_telemetry_stream.assert_called_once_with(stream, stream_path)
            mock_aggregator_stream.assert_called_once_with(stream, stream_path)

            self.assertEqual(t_res, telemetry_res_val)
            self.assertEqual(a_res, aggregator_res_val)

    def test_export_and_save_pipeline_artifacts(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("skills.system_health_telemetry_collector.SystemHealthTelemetryCollector.export_comprehensive_report") as mock_export, \
             patch("skills.system_health_aggregator.SystemHealthAggregator.save_dashboard_file") as mock_save:

            self.pipeline.export_and_save_pipeline_artifacts(payload, self.report_path, self.dashboard_path)

            mock_export.assert_called_once_with(payload, self.report_path)
            mock_save.assert_called_once_with(payload, self.dashboard_path)


if __name__ == "__main__":
    unittest.main()