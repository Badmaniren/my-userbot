import unittest
from unittest.mock import patch, mock_open
import json
import uuid
import random
import io

from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.output_path = f"{uuid.uuid4().hex}.json"
        self.html_output_path = f"{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex
        
        self.mock_metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        self.mock_text_rep = uuid.uuid4().hex
        self.mock_ascii_rep = uuid.uuid4().hex
        self.mock_digest_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        self.stability_digest_mock = unittest.mock.MagicMock()
        self.stability_digest_mock.export_digest_stream.return_value = self.mock_digest_data

        self.anomaly_visualizer_mock = unittest.mock.MagicMock()
        self.anomaly_visualizer_mock.get_summary_metrics.return_value = self.mock_metrics
        self.anomaly_visualizer_mock.render_text.return_value = self.mock_text_rep
        self.anomaly_visualizer_mock.render_ascii_correlation_graph.return_value = self.mock_ascii_rep
        self.anomaly_visualizer_mock.digest = self.mock_digest_data

        self.exporter = DigestExporter(
            stability_digest=self.stability_digest_mock,
            anomaly_visualizer=self.anomaly_visualizer_mock
        )

    def test_export_json_report_success(self):
        m = mock_open()
        with patch("builtins.open", m):
            result_path = self.exporter.export_json_report(self.output_path)
            
            self.assertEqual(result_path, self.output_path)
            m.assert_called_once_with(self.output_path, "w", encoding="utf-8")
            
            handle = m()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)
            
            self.assertEqual(parsed_json["text_report"], self.mock_text_rep)
            self.assertEqual(parsed_json["ascii_graph"], self.mock_ascii_rep)
            for k, v in self.mock_metrics.items():
                self.assertEqual(parsed_json[k], v)

    def test_export_json_report_exception_handling(self):
        self.anomaly_visualizer_mock.get_summary_metrics.side_effect = RuntimeError(uuid.uuid4().hex)
        
        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(self.output_path)

    def test_export_html_report_success(self):
        m = mock_open()
        with patch("builtins.open", m):
            result_path = self.exporter.export_html_report(self.html_output_path)
            
            self.assertEqual(result_path, self.html_output_path)
            m.assert_called_once_with(self.html_output_path, "w", encoding="utf-8")
            
            handle = m()
            written_content = "".join(call.args[0] for call in handle.write.mock_calls)
            
            self.assertIn("<html>", written_content)
            self.assertIn(self.mock_text_rep, written_content)
            self.assertIn(self.mock_ascii_rep, written_content)

    def test_export_html_report_exception_handling(self):
        self.anomaly_visualizer_mock.render_text.side_effect = ValueError(uuid.uuid4().hex)
        
        with self.assertRaises(DigestExporterError):
            self.exporter.export_html_report(self.html_output_path)

    def test_export_stream_to_json_success(self):
        m = mock_open()
        with patch("builtins.open", m):
            result_path = self.exporter.export_stream_to_json(self.stream_id, self.output_path)
            
            self.assertEqual(result_path, self.output_path)
            self.stability_digest_mock.export_digest_stream.assert_called_once_with(self.stream_id)
            
            m.assert_called_once_with(self.output_path, "w", encoding="utf-8")
            handle = m()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)
            
            self.assertEqual(parsed_json, self.mock_digest_data)

    def test_export_stream_to_json_exception_handling(self):
        self.stability_digest_mock.export_digest_stream.side_effect = KeyError(uuid.uuid4().hex)
        
        with self.assertRaises(DigestExporterError):
            self.exporter.export_stream_to_json(self.stream_id, self.output_path)

    def test_export_to_json_adapter_success(self):
        m = mock_open()
        with patch("builtins.open", m):
            result_path = self.exporter.export_to_json(self.output_path)
            
            self.assertEqual(result_path, self.output_path)
            m.assert_called_once_with(self.output_path, "w", encoding="utf-8")
            
            handle = m()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)
            
            self.assertEqual(parsed_json, self.mock_digest_data)

    def test_export_to_json_adapter_no_digest(self):
        self.anomaly_visualizer_mock.digest = None
        m = mock_open()
        with patch("builtins.open", m):
            result_path = self.exporter.export_to_json(self.output_path)
            
            self.assertEqual(result_path, self.output_path)
            handle = m()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)
            
            self.assertEqual(parsed_json, {})

    def test_export_to_html_adapter_success(self):
        m = mock_open()
        with patch("builtins.open", m):
            result_path = self.exporter.export_to_html(self.html_output_path)
            
            self.assertEqual(result_path, self.html_output_path)
            m.assert_called_once_with(self.html_output_path, "w", encoding="utf-8")
            
            handle = m()
            written_content = "".join(call.args[0] for call in handle.write.mock_calls)
            
            self.assertIn("<html><body><pre>", written_content)
            self.assertIn(json.dumps(self.mock_digest_data), written_content)

    def test_export_to_html_adapter_exception_handling(self):
        with patch("json.dumps", side_effect=TypeError(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_html(self.html_output_path)


if __name__ == "__main__":
    unittest.main()