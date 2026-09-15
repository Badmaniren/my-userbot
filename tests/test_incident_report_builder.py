import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.incident_report_builder import IncidentReportBuilder

class TestIncidentReportBuilder(unittest.TestCase):

    def setUp(self):
        self.builder = IncidentReportBuilder()
        self.random_incident_id = uuid.uuid4().hex
        self.random_module_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_error_msg = ''.join(random.choices(string.ascii_letters + string.space, k=25))
        self.random_output_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.random_format = random.choice(["json", "xml", "csv", "yaml"])

    def test_composition_and_initialization(self):
        self.assertIsNotNone(self.builder, "Архитектор-Инквизитор недоволен: модуль не инициализирован.")
        self.assertTrue(hasattr(self.builder, 'metric_collector'), "Нарушение композиции: отсутствует patch_metric_collector")
        self.assertTrue(hasattr(self.builder, 'audit_reporter'), "Нарушение композиции: отсутствует dependency_audit_reporter")

    def test_build_incident_report_success(self):
        random_metric_payload = {
            "incident_id": self.random_incident_id,
            "module": self.random_module_name,
            "success": True,
            "latency": random.uniform(0.1, 5.0)
        }
        random_audit_data = {
            "dependencies": [
                {"package": "requests", "installed": "2.28.1", "vulnerable": False},
                {"package": "urllib3", "installed": "1.26.5", "vulnerable": True}
            ],
            "scan_id": uuid.uuid4().hex
        }
        expected_report_str = json.dumps({
            "incident_id": self.random_incident_id,
            "status": "SECURE_AND_PATCHED"
        })

        with patch('skills.patch_metric_collector.PatchMetricCollector.record_metric') as mock_record, \
             patch('skills.dependency_audit_reporter.DependencyAuditReporter.generate_report') as mock_gen_report:

            mock_record.return_value = random_metric_payload
            mock_gen_report.return_value = expected_report_str

            if hasattr(self.builder, 'build_report'):
                result = self.builder.build_report(random_metric_payload, random_audit_data)
                self.assertIn(self.random_incident_id, str(result))
                mock_record.assert_called_once_with(random_metric_payload)
                mock_gen_report.assert_called_once_with(random_audit_data)
            else:
                self.fail("Метод build_report отсутствует в IncidentReportBuilder")

    def test_export_incident_analytics_chaos_data(self):
        random_stream_data = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)
        random_epic_id = f"EPIC-{random.randint(1000, 9999)}"

        with patch('skills.dependency_audit_reporter.DependencyAuditReporter.finalize_epic') as mock_finalize, \
             patch('skills.dependency_audit_reporter.DependencyAuditReporter.export_summary') as mock_export:

            mock_finalize.return_value = True
            mock_export.return_value = f"EXPORTED_{self.random_format.upper()}_{self.random_incident_id}"

            if hasattr(self.builder, 'export_analytics'):
                res = self.builder.export_analytics(random_epic_id, random_stream_data, self.random_format)
                self.assertIn(self.random_format.upper(), res)
                mock_finalize.assert_called_once_with(random_epic_id, random_stream_data)
            else:
                self.fail("Метод export_analytics отсутствует в IncidentReportBuilder")

    def test_generate_epic_incident_pipeline(self):
        random_payload = {
            "incident": self.random_incident_id,
            "error_trace": self.random_error_msg,
            "score": random.randint(1, 100)
        }

        with patch('skills.patch_metric_collector.PatchMetricCollector.get_metrics_summary') as mock_get_summary, \
             patch('skills.dependency_audit_reporter.DependencyAuditReporter.generate_epic_report') as mock_epic_gen:

            mock_get_summary.return_value = f"SUMMARY_FOR_{self.random_module_name}"
            mock_epic_gen.return_value = True

            if hasattr(self.builder, 'generate_epic_incident_pipeline'):
                success = self.builder.generate_epic_incident_pipeline(self.random_module_name, random_payload, self.random_output_path)
                self.assertTrue(success)
                mock_get_summary.assert_called_once_with(self.random_module_name)
                mock_epic_gen.assert_called_once()
            else:
                self.fail("Метод generate_epic_incident_pipeline отсутствует в IncidentReportBuilder")

    def test_metric_export_delegation(self):
        with patch('skills.patch_metric_collector.PatchMetricCollector.export_metrics') as mock_export_metrics:
            mock_export_metrics.return_value = True

            if hasattr(self.builder, 'export_raw_metrics'):
                res = self.builder.export_raw_metrics(self.random_output_path, self.random_format)
                self.assertTrue(res)
                mock_export_metrics.assert_called_once_with(self.random_output_path, self.random_format)
            else:
                self.fail("Метод export_raw_metrics отсутствует в IncidentReportBuilder")

if __name__ == '__main__':
    unittest.main()