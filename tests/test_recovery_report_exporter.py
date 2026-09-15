import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.recovery_report_exporter import RecoveryReportExporter

class TestRecoveryReportExporter(unittest.TestCase):

    def _generate_random_string(self, length=10):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def test_exporter_initialization_and_composition(self):
        with patch('skills.recovery_report_exporter.IncidentAggregator') as mock_aggregator_cls, \
             patch('skills.recovery_report_exporter.DependencyAuditReporter') as mock_reporter_cls:
            
            mock_aggregator_instance = mock_aggregator_cls.return_value
            mock_reporter_instance = mock_reporter_cls.return_value

            exporter = RecoveryReportExporter()

            mock_aggregator_cls.assert_called_once()
            mock_reporter_cls.assert_called_once()
            self.assertEqual(exporter.aggregator, mock_aggregator_instance)
            self.assertEqual(exporter.reporter, mock_reporter_instance)

    def test_generate_comprehensive_report_success(self):
        rand_module = self._generate_random_string(12)
        rand_exc_msg = self._generate_random_string(20)
        rand_tb = self._generate_random_string(30)
        rand_incident_id = str(uuid.uuid4())
        rand_audit_data = {self._generate_random_string(5): self._generate_random_string(5)}
        rand_aggregated_result = {self._generate_random_string(4): self._generate_random_string(6)}
        rand_report_output = self._generate_random_string(15)

        with patch('skills.recovery_report_exporter.IncidentAggregator') as mock_aggregator_cls, \
             patch('skills.recovery_report_exporter.DependencyAuditReporter') as mock_reporter_cls:
            
            mock_aggregator_instance = mock_aggregator_cls.return_value
            mock_aggregator_instance.process_and_aggregate.return_value = rand_aggregated_result

            mock_reporter_instance = mock_reporter_cls.return_value
            mock_reporter_instance.generate_report.return_value = rand_report_output

            exporter = RecoveryReportExporter()
            
            exception_obj = Exception(rand_exc_msg)
            result = exporter.generate_comprehensive_report(
                module_name=rand_module,
                exception=exception_obj,
                traceback_str=rand_tb,
                incident_id=rand_incident_id,
                audit_data=rand_audit_data
            )

            mock_aggregator_instance.process_and_aggregate.assert_called_once_with(
                rand_module, exception_obj, rand_tb, rand_incident_id
            )
            mock_reporter_instance.generate_report.assert_called_once_with(rand_audit_data)

            self.assertIn('incident_analytics', result)
            self.assertIn('dependency_report', result)
            self.assertEqual(result['incident_analytics'], rand_aggregated_result)
            self.assertEqual(result['dependency_report'], rand_report_output)

    def test_export_complex_summary_stream(self):
        rand_stream_data = io.BytesIO(self._generate_random_string(50).encode('utf-8'))
        rand_epic_id = self._generate_random_string(8)
        rand_summary_payload = {self._generate_random_string(4): self._generate_random_string(8)}
        rand_format = random.choice(['json', 'xml', 'pdf', 'csv'])
        rand_export_result = self._generate_random_string(25)

        with patch('skills.recovery_report_exporter.IncidentAggregator') as mock_aggregator_cls, \
             patch('skills.recovery_report_exporter.DependencyAuditReporter') as mock_reporter_cls:
            
            mock_aggregator_instance = mock_aggregator_cls.return_value
            mock_reporter_instance = mock_reporter_cls.return_value
            mock_reporter_instance.export_summary.return_value = rand_export_result
            mock_reporter_instance.finalize_epic.return_value = True

            exporter = RecoveryReportExporter()
            
            finalized = exporter.finalize_and_export_summary(
                epic_id=rand_epic_id,
                stream=rand_stream_data,
                summary_payload=rand_summary_payload,
                export_format=rand_format
            )

            mock_reporter_instance.finalize_epic.assert_called_once_with(rand_epic_id, rand_stream_data)
            mock_reporter_instance.export_summary.assert_called_once_with(rand_summary_payload, rand_format)
            self.assertTrue(finalized['epic_finalized'])
            self.assertEqual(finalized['summary_export'], rand_export_result)

    def test_export_epic_report_pipeline(self):
        rand_report_payload = {self._generate_random_string(6): random.randint(1, 100)}
        rand_output_path = f"/{self._generate_random_string(5)}/{self._generate_random_string(8)}.rpt"

        with patch('skills.recovery_report_exporter.IncidentAggregator') as mock_aggregator_cls, \
             patch('skills.recovery_report_exporter.DependencyAuditReporter') as mock_reporter_cls:
            
            mock_reporter_instance = mock_reporter_cls.return_value
            mock_reporter_instance.generate_epic_report.return_value = True

            exporter = RecoveryReportExporter()
            success = exporter.export_epic_report_file(rand_report_payload, rand_output_path)

            mock_reporter_instance.generate_epic_report.assert_called_once_with(rand_report_payload, rand_output_path)
            self.assertTrue(success)

if __name__ == '__main__':
    unittest.main()