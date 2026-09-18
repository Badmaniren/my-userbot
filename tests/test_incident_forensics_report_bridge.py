import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.incident_forensics_report_bridge import IncidentForensicsReportBridge


class TestIncidentForensicsReportBridge(unittest.TestCase):

    def setUp(self):
        self.rand_incident_id = str(uuid.uuid4())
        self.rand_module_name = "".join(random.choices(string.ascii_lowercase, k=10))
        self.rand_traceback = "".join(random.choices(string.ascii_letters + string.whitespace, k=30))
        self.rand_export_path = f"/var/reports/{uuid.uuid4().hex}.json"
        self.rand_format_type = random.choice(["json", "pdf", "html", "csv"])
        
        self.financial_evaluator_mock = MagicMock()
        self.impact_analyzer_mock = MagicMock()
        
        self.bridge = IncidentForensicsReportBridge(
            financial_evaluator=self.financial_evaluator_mock,
            impact_analyzer=self.impact_analyzer_mock
        )

    def test_bridge_composition_initialization(self):
        self.assertIsNotNone(self.bridge.forensics_synthesizer)
        self.assertIsNotNone(self.bridge.business_loss_reporter)

    @patch('skills.incident_forensics_report_bridge.IncidentForensicsSynthesizer')
    @patch('skills.incident_forensics_report_bridge.IncidentBusinessLossReporter')
    def test_generate_comprehensive_report_success(self, mock_reporter_cls, mock_synthesizer_cls):
        synth_instance = mock_synthesizer_cls.return_value
        rand_synth_result = {
            "incident_id": self.rand_incident_id,
            "module": self.rand_module_name,
            "status": "synthesized"
        }
        synth_instance.synthesize.return_value = rand_synth_result

        reporter_instance = mock_reporter_cls.return_value
        rand_report_data = {
            "report_id": str(uuid.uuid4()),
            "loss_estimation": random.randint(1000, 999999)
        }
        reporter_instance.generate_report.return_value = rand_report_data

        rand_export_result = f"Exported successfully to {self.rand_export_path}"
        reporter_instance.export_report.return_value = rand_export_result

        dummy_exception = Exception("".join(random.choices(string.ascii_letters, k=8)))

        bridge_instance = IncidentForensicsReportBridge(
            financial_evaluator=self.financial_evaluator_mock,
            impact_analyzer=self.impact_analyzer_mock
        )
        bridge_instance.forensics_synthesizer = synth_instance
        bridge_instance.business_loss_reporter = reporter_instance

        result = bridge_instance.generate_comprehensive_report(
            incident_id=self.rand_incident_id,
            module_name=self.rand_module_name,
            exception=dummy_exception,
            traceback_str=self.rand_traceback,
            financial_data={"downtime_hours": random.randint(1, 24)},
            export_path=self.rand_export_path,
            format_type=self.rand_format_type
        )

        synth_instance.synthesize.assert_called_once_with(
            module_name=self.rand_module_name,
            exception=dummy_exception,
            traceback_str=self.rand_traceback,
            incident_id=self.rand_incident_id
        )

        reporter_instance.generate_report.assert_called_once()
        reporter_instance.export_report.assert_called_once_with(rand_report_data, self.rand_format_type)

        self.assertIn("forensics", result)
        self.assertIn("business_loss", result)
        self.assertIn("export_status", result)
        self.assertEqual(result["forensics"], rand_synth_result)
        self.assertEqual(result["business_loss"], rand_report_data)
        self.assertEqual(result["export_status"], rand_export_result)

    def test_bridge_handles_synthesizer_failure(self):
        dummy_exception = RuntimeError(uuid.uuid4().hex)

        with patch.object(self.bridge.forensics_synthesizer, 'synthesize', side_effect=Exception("Synthesis crashed")) as mock_synth:
            with patch.object(self.bridge.business_loss_reporter, 'generate_report') as mock_gen_rep:
                with self.assertRaises(Exception):
                    self.bridge.generate_comprehensive_report(
                        incident_id=self.rand_incident_id,
                        module_name=self.rand_module_name,
                        exception=dummy_exception,
                        traceback_str=self.rand_traceback,
                        financial_data={},
                        export_path=self.rand_export_path,
                        format_type=self.rand_format_type
                    )
                mock_gen_rep.assert_not_called()

    def test_stream_forensics_and_loss_report(self):
        rand_stream_data = "".join(random.choices(string.printable, k=50)).encode('utf-8')
        mock_stream = io.BytesIO(rand_stream_data)

        with patch.object(self.bridge.business_loss_reporter, 'export_report', return_value=mock_stream) as mock_export:
            rand_format = random.choice(["csv", "json"])
            res_stream = self.bridge.stream_report_package(
                incident_id=self.rand_incident_id,
                financial_data={"metric": random.random()},
                format_type=rand_format
            )
            
            content = res_stream.read()
            self.assertEqual(content, rand_stream_data)
            mock_export.assert_called_once()