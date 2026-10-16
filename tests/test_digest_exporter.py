import unittest
from unittest.mock import patch, MagicMock, mock_open
import uuid
import random
import string
import io
import json

from skills.digest_exporter import DigestExporter, DigestExporterError
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.stability_digest import StabilityDigest

class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.output_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.html_output_path = f"/tmp/{uuid.uuid4().hex}.html"
        self.execution_id = uuid.uuid4().hex
        self.stream_id = uuid.uuid4().hex
        self.metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        
        self.mock_detector = MagicMock()
        self.mock_telemetry = MagicMock()
        
        self.digest_instance = StabilityDigest(
            repo_path=self.repo_path,
            anomaly_detector=self.mock_detector,
            system_telemetry=self.mock_telemetry
        )
        self.visualizer_instance = AnomalyVisualizer(digest=self.digest_instance)

    def test_digest_exporter_initialization(self):
        exporter = DigestExporter(
            stability_digest=self.digest_instance,
            anomaly_visualizer=self.visualizer_instance
        )
        self.assertIs(exporter.digest, self.digest_instance)
        self.assertIs(exporter.visualizer, self.visualizer_instance)

    def test_export_json_report_success(self):
        random_summary_val = random.randint(100, 999)
        mock_summary = {self.metric_name: random_summary_val}
        mock_text = f"TEXT_{uuid.uuid4().hex}"
        mock_ascii = f"ASCII_{uuid.uuid4().hex}"

        with patch.object(AnomalyVisualizer, 'get_summary_metrics', return_value=mock_summary) as m_metrics, \
             patch.object(AnomalyVisualizer, 'render_text', return_value=mock_text) as m_text, \
             patch.object(AnomalyVisualizer, 'render_ascii_correlation_graph', return_value=mock_ascii) as m_ascii, \
             patch('builtins.open', new_callable=mock_open()) as m_file:

            exporter = DigestExporter(
                stability_digest=self.digest_instance,
                anomaly_visualizer=self.visualizer_instance
            )
            
            result_path = exporter.export_json_report(self.output_path)
            
            self.assertEqual(result_path, self.output_path)
            m_metrics.assert_called_once()
            m_text.assert_called_once()
            m_ascii.assert_called_once()
            m_file.assert_called_once_with(self.output_path, 'w', encoding='utf-8')
            
            handle = m_file()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_json = json.loads(written_data)
            
            self.assertEqual(parsed_json[self.metric_name], random_summary_val)
            self.assertEqual(parsed_json['text_report'], mock_text)
            self.assertEqual(parsed_json['ascii_graph'], mock_ascii)

    def test_export_html_report_success(self):
        random_title_suffix = uuid.uuid4().hex[:6]
        mock_summary = {self.metric_name: random.random()}
        mock_text = f"HTML_TEXT_{uuid.uuid4().hex}"
        mock_ascii = f"HTML_ASCII_{uuid.uuid4().hex}"

        with patch.object(AnomalyVisualizer, 'get_summary_metrics', return_value=mock_summary), \
             patch.object(AnomalyVisualizer, 'render_text', return_value=mock_text), \
             patch.object(AnomalyVisualizer, 'render_ascii_correlation_graph', return_value=mock_ascii), \
             patch('builtins.open', new_callable=mock_open()) as m_file:

            exporter = DigestExporter(
                stability_digest=self.digest_instance,
                anomaly_visualizer=self.visualizer_instance
            )
            
            result_path = exporter.export_html_report(self.html_output_path)
            
            self.assertEqual(result_path, self.html_output_path)
            m_file.assert_called_once_with(self.html_output_path, 'w', encoding='utf-8')
            
            handle = m_file()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            
            self.assertIn("<html>", written_data.lower())
            self.assertIn(mock_text, written_data)
            self.assertIn(mock_ascii, written_data)
            self.assertIn(self.metric_name, written_data)

    def test_export_json_report_raises_exception(self):
        random_err_msg = f"ERROR_{uuid.uuid4().hex}"
        
        with patch.object(AnomalyVisualizer, 'get_summary_metrics', side_effect=Exception(random_err_msg)):
            exporter = DigestExporter(
                stability_digest=self.digest_instance,
                anomaly_visualizer=self.visualizer_instance
            )
            
            with self.assertRaises(DigestExporterError) as ctx:
                exporter.export_json_report(self.output_path)
            
            self.assertIn(random_err_msg, str(ctx.exception))

    def test_export_html_report_raises_exception(self):
        random_err_msg = f"ERR_HTML_{uuid.uuid4().hex}"
        
        with patch.object(AnomalyVisualizer, 'render_text', side_effect=Exception(random_err_msg)):
            exporter = DigestExporter(
                stability_digest=self.digest_instance,
                anomaly_visualizer=self.visualizer_instance
            )
            
            with self.assertRaises(DigestExporterError) as ctx:
                exporter.export_html_report(self.html_output_path)
            
            self.assertIn(random_err_msg, str(ctx.exception))

    def test_stream_digest_export_integration(self):
        random_stream_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        
        with patch.object(StabilityDigest, 'export_digest_stream', return_value=random_stream_data) as m_stream:
            exporter = DigestExporter(
                stability_digest=self.digest_instance,
                anomaly_visualizer=self.visualizer_instance
            )
            
            result = exporter.export_stream_to_json(self.stream_id, self.output_path)
            
            m_stream.assert_called_once_with(self.stream_id)
            self.assertEqual(result, self.output_path)

if __name__ == '__main__':
    unittest.main()