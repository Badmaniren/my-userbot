import unittest
from unittest.mock import patch, mock_open
import random
import uuid
import string
import io
from skills.incident_report_builder import IncidentReportBuilder

class TestIncidentReportBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = IncidentReportBuilder()
        self.random_metric_payload = {str(uuid.uuid4().hex): random.randint(1, 100)}
        self.random_audit_data = {str(uuid.uuid4().hex): str(uuid.uuid4().hex)}
        self.random_epic_id = str(uuid.uuid4().hex)
        self.random_stream_data = str(uuid.uuid4().hex)
        self.random_format = random.choice(["json", "csv", "xml"])
        self.random_module_name = str(uuid.uuid4().hex)
        self.random_payload = {str(uuid.uuid4().hex): str(uuid.uuid4().hex)}
        self.random_output_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.txt"
        self.random_summary_payload = str(uuid.uuid4().hex)

    def test_composition_and_initialization(self):
        self.assertIsNotNone(self.builder.metric_collector)
        self.assertIsNotNone(self.builder.audit_reporter)
        from skills.patch_metric_collector import PatchMetricCollector
        from skills.dependency_audit_reporter import DependencyAuditReporter
        self.assertIsInstance(self.builder.metric_collector, PatchMetricCollector)
        self.assertIsInstance(self.builder.audit_reporter, DependencyAuditReporter)

    def test_build_report_success(self):
        expected_recorded = {str(uuid.uuid4().hex): random.randint(100, 999)}
        expected_report = str(uuid.uuid4().hex)

        with patch.object(self.builder.metric_collector, 'record_metric', return_value=expected_recorded) as mock_record, \
             patch.object(self.builder.audit_reporter, 'generate_report', return_value=expected_report) as mock_generate:

            result = self.builder.build_report(self.random_metric_payload, self.random_audit_data)

            mock_record.assert_called_once_with(self.random_metric_payload)
            mock_generate.assert_called_once_with(self.random_audit_data)
            self.assertEqual(result, f"{expected_recorded} {expected_report}")

    def test_export_analytics(self):
        expected_export = str(uuid.uuid4().hex)

        with patch.object(self.builder.audit_reporter, 'finalize_epic', return_value=True) as mock_finalize, \
             patch.object(self.builder.audit_reporter, 'export_summary', return_value=expected_export) as mock_export:

            result = self.builder.export_analytics(self.random_epic_id, self.random_stream_data, self.random_format)

            mock_finalize.assert_called_once()
            call_args = mock_finalize.call_args[0]
            self.assertEqual(call_args[0], self.random_epic_id)
            self.assertIsInstance(call_args[1], io.BytesIO)
            self.assertEqual(call_args[1].getvalue(), self.random_stream_data.encode("utf-8"))

            mock_export.assert_called_once_with(self.random_epic_id, self.random_stream_data, self.random_format)
            self.assertEqual(result, expected_export)

    def test_generate_epic_incident_pipeline(self):
        expected_summary = str(uuid.uuid4().hex)
        expected_pipeline_result = True

        with patch.object(self.builder.metric_collector, 'get_metrics_summary', return_value=expected_summary) as mock_get_metrics, \
             patch.object(self.builder.audit_reporter, 'generate_epic_report', return_value=expected_pipeline_result) as mock_generate_epic:

            result = self.builder.generate_epic_incident_pipeline(self.random_module_name, self.random_payload, self.random_output_path)

            mock_get_metrics.assert_called_once_with(self.random_module_name)
            mock_generate_epic.assert_called_once_with(self.random_module_name, self.random_payload, self.random_output_path)
            self.assertEqual(result, expected_pipeline_result)

    def test_export_raw_metrics(self):
        expected_result = random.choice([True, False])

        with patch.object(self.builder.metric_collector, 'export_metrics', return_value=expected_result) as mock_export:
            result = self.builder.export_raw_metrics(self.random_output_path, self.random_format)

            mock_export.assert_called_once_with(self.random_output_path, self.random_format)
            self.assertEqual(result, expected_result)

    def test_generate_summary_report(self):
        result = self.builder.generate_summary_report(self.random_summary_payload)
        self.assertEqual(result, str(self.random_summary_payload))

    def test_export_incident_report(self):
        m = mock_open()
        with patch("builtins.open", m):
            result = self.builder.export_incident_report(self.random_summary_payload, self.random_output_path)

            m.assert_called_once_with(self.random_output_path, "w")
            m().write.assert_called_once_with(str(self.random_summary_payload))
            self.assertTrue(result)

if __name__ == "__main__":
    unittest.main()