import unittest
from unittest.mock import patch, MagicMock, call
import uuid
import random
import string
import io

from skills.system_health_monitoring_gateway import SystemHealthMonitoringGateway
from skills.system_health_audit_pipeline import SystemHealthAuditPipeline
from skills.system_health_reporter import SystemHealthReporter


class TestSystemHealthMonitoringGateway(unittest.TestCase):

    def setUp(self):
        self.gateway = SystemHealthMonitoringGateway()

    def test_gateway_initialization_and_composition(self):
        self.assertIsInstance(self.gateway.audit_pipeline, SystemHealthAuditPipeline)
        self.assertIsInstance(self.gateway.reporter, SystemHealthReporter)

    def test_run_monitoring_gateway_pipeline(self):
        rand_module = uuid.uuid4().hex
        rand_inc_key = uuid.uuid4().hex
        rand_inc_val = random.randint(100, 999)
        incident_data = {rand_inc_key: rand_inc_val}
        
        rand_audit_key = uuid.uuid4().hex
        audit_summary = {rand_audit_key: random.choice(string.ascii_letters)}
        
        rand_metric_key = uuid.uuid4().hex
        metrics = {rand_metric_key: random.random()}
        
        dashboard_format = uuid.uuid4().hex
        incidents_list = [uuid.uuid4().hex, uuid.uuid4().hex]
        patches_list = [uuid.uuid4().hex, uuid.uuid4().hex]
        report_path = f"/tmp/{uuid.uuid4().hex}.json"
        dashboard_path = f"/tmp/{uuid.uuid4().hex}.html"

        expected_pipeline_result = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "status": uuid.uuid4().hex
        }

        with patch.object(
            SystemHealthAuditPipeline, 
            'run_audit_pipeline', 
            return_value=expected_pipeline_result
        ) as mock_run_pipeline:
            
            result = self.gateway.run_monitoring_gateway_pipeline(
                module_name=rand_module,
                incident_data=incident_data,
                audit_summary=audit_summary,
                metrics=metrics,
                dashboard_format=dashboard_format,
                incidents_list=incidents_list,
                patches_list=patches_list,
                report_path=report_path,
                dashboard_path=dashboard_path
            )

            mock_run_pipeline.assert_called_once_with(
                rand_module,
                incident_data,
                audit_summary,
                metrics,
                dashboard_format,
                incidents_list,
                patches_list,
                report_path,
                dashboard_path
            )
            self.assertEqual(result, expected_pipeline_result)

    def test_process_monitoring_gateway_stream(self):
        rand_stream_content = uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(rand_stream_content)
        stream_path = f"/var/log/{uuid.uuid4().hex}.log"

        expected_stream_result = {
            uuid.uuid4().hex: random.randint(1, 100)
        }

        with patch.object(
            SystemHealthAuditPipeline,
            'process_audit_stream',
            return_value=expected_stream_result
        ) as mock_process_stream:

            result = self.gateway.process_monitoring_gateway_stream(stream, stream_path)

            mock_process_stream.assert_called_once_with(stream, stream_path)
            self.assertEqual(result, expected_stream_result)

    def test_export_monitoring_gateway_artifacts(self):
        rand_payload_key = uuid.uuid4().hex
        rand_payload_val = uuid.uuid4().hex
        payload = {rand_payload_key: rand_payload_val}
        report_path = f"/reports/{uuid.uuid4().hex}.rpt"
        dashboard_path = f"/dashboards/{uuid.uuid4().hex}.dash"

        expected_export_result = uuid.uuid4().hex

        with patch.object(
            SystemHealthAuditPipeline,
            'export_and_save_pipeline_artifacts',
            return_value=expected_export_result
        ) as mock_export_artifacts:

            result = self.gateway.export_monitoring_gateway_artifacts(
                payload, report_path, dashboard_path
            )

            mock_export_artifacts.assert_called_once_with(
                payload, report_path, dashboard_path
            )
            self.assertEqual(result, expected_export_result)

    def test_generate_gateway_health_report(self):
        module_name = uuid.uuid4().hex
        incident_data = {uuid.uuid4().hex: random.randint(1, 50)}
        audit_summary = {uuid.uuid4().hex: uuid.uuid4().hex}
        metrics = {uuid.uuid4().hex: random.random()}

        expected_report = {
            uuid.uuid4().hex: uuid.uuid4().hex
        }

        with patch.object(
            SystemHealthReporter,
            'generate_health_report',
            return_value=expected_report
        ) as mock_gen_report:

            result = self.gateway.generate_gateway_health_report(
                module_name, incident_data, audit_summary, metrics
            )

            mock_gen_report.assert_called_once_with(
                module_name, incident_data, audit_summary, metrics
            )
            self.assertEqual(result, expected_report)

    def test_parse_gateway_stream_data(self):
        stream_content = uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(stream_content)

        expected_parsed = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch.object(
            SystemHealthReporter,
            'parse_stream_data',
            return_value=expected_parsed
        ) as mock_parse:

            result = self.gateway.parse_gateway_stream_data(stream)

            mock_parse.assert_called_once_with(stream)
            self.assertEqual(result, expected_parsed)

    def test_export_gateway_report_file(self):
        payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        file_path = f"/exports/{uuid.uuid4().hex}.json"
        expected_ret = uuid.uuid4().hex

        with patch.object(
            SystemHealthReporter,
            'export_report_file',
            return_value=expected_ret
        ) as mock_export:

            result = self.gateway.export_gateway_report_file(payload, file_path)

            mock_export.assert_called_once_with(payload, file_path)
            self.assertEqual(result, expected_ret)

    def test_export_gateway_health_report(self):
        health_report = {uuid.uuid4().hex: uuid.uuid4().hex}
        file_path = f"/exports/{uuid.uuid4().hex}.yaml"
        expected_ret = uuid.uuid4().hex

        with patch.object(
            SystemHealthReporter,
            'export_health_report',
            return_value=expected_ret
        ) as mock_export_health:

            result = self.gateway.export_gateway_health_report(health_report, file_path)

            mock_export_health.assert_called_once_with(health_report, file_path)
            self.assertEqual(result, expected_ret)

    def test_aggregate_gateway_system_metrics(self):
        incidents_list = [uuid.uuid4().hex, uuid.uuid4().hex]
        patches_list = [uuid.uuid4().hex]
        expected_metrics = {uuid.uuid4().hex: random.randint(100, 999)}

        with patch.object(
            SystemHealthReporter,
            'aggregate_system_metrics',
            return_value=expected_metrics
        ) as mock_aggregate:

            result = self.gateway.aggregate_gateway_system_metrics(
                incidents_list, patches_list
            )

            mock_aggregate.assert_called_once_with(incidents_list, patches_list)
            self.assertEqual(result, expected_metrics)


if __name__ == '__main__':
    unittest.main()