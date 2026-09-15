import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.incident_aggregator import IncidentAggregator
from skills.patch_metric_collector import PatchMetricCollector
from skills.dependency_audit_reporter import DependencyAuditReporter


class TestIncidentAggregator(unittest.TestCase):

    def setUp(self):
        self.metric_collector_mock = MagicMock(spec=PatchMetricCollector)
        self.audit_reporter_mock = MagicMock(spec=DependencyAuditReporter)
        self.aggregator = IncidentAggregator(
            metric_collector=self.metric_collector_mock,
            audit_reporter=self.audit_reporter_mock
        )

    def test_init_default_dependencies(self):
        aggregator_default = IncidentAggregator()
        self.assertIsInstance(aggregator_default.metric_collector, PatchMetricCollector)
        self.assertIsInstance(aggregator_default.audit_reporter, DependencyAuditReporter)

    def test_aggregate_and_report_delegation(self):
        module_name = uuid.uuid4().hex
        export_format = random.choice(['json', 'csv', 'pdf', 'xml'])

        expected_metrics = uuid.uuid4().hex
        expected_audit = uuid.uuid4().hex
        expected_export_result = uuid.uuid4().hex

        self.metric_collector_mock.get_metrics_summary.return_value = expected_metrics
        self.audit_reporter_mock.generate_report.return_value = expected_audit
        self.audit_reporter_mock.export_summary.return_value = expected_export_result

        result = self.aggregator.aggregate_and_report(module_name, export_format)

        self.metric_collector_mock.get_metrics_summary.assert_called_once_with(module_name)
        self.audit_reporter_mock.generate_report.assert_called_once_with(module_name)

        expected_payload = {
            'module_name': module_name,
            'metrics_summary': expected_metrics,
            'audit_report': expected_audit
        }
        self.audit_reporter_mock.export_summary.assert_called_once_with(expected_payload, export_format)
        self.assertEqual(result, expected_export_result)

    def test_record_incident_metric_delegation(self):
        payload = {
            'incident_id': uuid.uuid4().hex,
            'error': uuid.uuid4().hex,
            'status': random.choice([True, False])
        }
        expected_return = {'status': uuid.uuid4().hex}
        self.metric_collector_mock.record_metric.return_value = expected_return

        result = self.aggregator.record_incident_metric(payload)

        self.metric_collector_mock.record_metric.assert_called_once_with(payload)
        self.assertEqual(result, expected_return)

    def test_finalize_health_epic_delegation(self):
        epic_id = uuid.uuid4().hex
        rand_chars = string.ascii_letters + string.digits
        stream_data = ''.join(random.choices(rand_chars, k=50)).encode('utf-8')
        stream = io.BytesIO(stream_data)

        expected_bool = random.choice([True, False])
        self.audit_reporter_mock.finalize_epic.return_value = expected_bool

        result = self.aggregator.finalize_health_epic(epic_id, stream)

        self.audit_reporter_mock.finalize_epic.assert_called_once_with(epic_id, stream)
        self.assertEqual(result, expected_bool)

    def test_export_system_health_metrics_delegation(self):
        path = f"/var/log/{uuid.uuid4().hex}.json"
        format_type = random.choice(['json', 'yaml'])
        expected_bool = random.choice([True, False])

        self.metric_collector_mock.export_metrics.return_value = expected_bool

        result = self.aggregator.export_system_health_metrics(path, format_type)

        self.metric_collector_mock.export_metrics.assert_called_once_with(path, format_type)
        self.assertEqual(result, expected_bool)

    def test_generate_epic_health_report_delegation(self):
        payload = {'epic_id': uuid.uuid4().hex, 'data': uuid.uuid4().hex}
        path = f"/tmp/{uuid.uuid4().hex}.report"
        expected_bool = random.choice([True, False])

        self.audit_reporter_mock.generate_epic_report.return_value = expected_bool

        result = self.aggregator.generate_epic_report(payload, path)

        self.audit_reporter_mock.generate_epic_report.assert_called_once_with(payload, path)
        self.assertEqual(result, expected_bool)

    def test_generate_health_report_logic(self):
        module_name = uuid.uuid4().hex
        incident_id = uuid.uuid4().hex
        audit_data = {'audit_info': uuid.uuid4().hex}
        metrics_payload = {'incident_id': incident_id}

        metrics_summary = uuid.uuid4().hex
        audit_report = uuid.uuid4().hex

        self.metric_collector_mock.get_metrics_summary.return_value = metrics_summary
        self.audit_reporter_mock.generate_report.return_value = audit_report

        result = self.aggregator.generate_health_report(module_name, audit_data, metrics_payload)

        self.metric_collector_mock.get_metrics_summary.assert_called_once_with(module_name)
        self.audit_reporter_mock.generate_report.assert_called_once_with(audit_data)

        self.assertIn(module_name, result)
        self.assertIn(incident_id, result)
        self.assertIn(metrics_summary, result)
        self.assertIn(audit_report, result)

    def test_generate_health_report_string_audit_data(self):
        module_name = uuid.uuid4().hex
        incident_id = uuid.uuid4().hex
        audit_data = f"audit_str_{uuid.uuid4().hex}"
        metrics_payload = {'incident_id': incident_id}

        metrics_summary = uuid.uuid4().hex
        audit_report = uuid.uuid4().hex

        self.metric_collector_mock.get_metrics_summary.return_value = metrics_summary
        self.audit_reporter_mock.generate_report.return_value = audit_report

        result = self.aggregator.generate_health_report(module_name, audit_data, metrics_payload)

        self.metric_collector_mock.get_metrics_summary.assert_called_once_with(module_name)
        self.audit_reporter_mock.generate_report.assert_called_once_with(audit_data)

        self.assertIn(module_name, result)
        self.assertIn(incident_id, result)
        self.assertIn(metrics_summary, result)
        self.assertIn(audit_report, result)

    def test_aggregate_and_report_with_patch_context(self):
        module_name = uuid.uuid4().hex
        export_format = uuid.uuid4().hex

        with patch.object(self.metric_collector_mock, 'get_metrics_summary', return_value="mock_metrics") as m_sum, \
             patch.object(self.audit_reporter_mock, 'generate_report', return_value="mock_audit") as a_rep, \
             patch.object(self.audit_reporter_mock, 'export_summary', return_value="mock_export") as a_exp:

            res = self.aggregator.aggregate_and_report(module_name, export_format)

            m_sum.assert_called_once_with(module_name)
            a_rep.assert_called_once_with(module_name)
            a_exp.assert_called_once()
            self.assertEqual(res, "mock_export")