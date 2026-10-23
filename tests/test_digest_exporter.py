import unittest
from unittest.mock import patch, mock_open
import json
import uuid
import random
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.output_path = f"{uuid.uuid4().hex}.json"
        self.html_output_path = f"{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex
        
        self.mock_metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        self.text_rep = uuid.uuid4().hex
        self.ascii_rep = uuid.uuid4().hex
        self.digest_data = {uuid.uuid4().hex: uuid.uuid4().hex}

        self.stability_digest_mock = unittest.mock.MagicMock()
        self.stability_digest_mock.export_digest_stream.return_value = self.digest_data

        self.anomaly_visualizer_mock = unittest.mock.MagicMock()
        self.anomaly_visualizer_mock.get_summary_metrics.return_value = self.mock_metrics
        self.anomaly_visualizer_mock.render_text.return_value = self.text_rep
        self.anomaly_visualizer_mock.render_ascii_correlation_graph.return_value = self.ascii_rep
        self.anomaly_visualizer_mock.digest = self.digest_data

        self.exporter = DigestExporter(
            stability_digest=self.stability_digest_mock,
            anomaly_visualizer=self.anomaly_visualizer_mock
        )

    def test_export_json_report_success(self):
        m_open = mock_open()
        with patch("builtins.open", m_open):
            result = self.exporter.export_json_report(self.output_path)
            
            self.assertEqual(result, self.output_path)
            m_open.assert_called_once_with(self.output_path, "w", encoding="utf-8")
            
            handle = m_open()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)
            
            self.assertIn("text_report", parsed_json)
            self.assertEqual(parsed_json["text_report"], self.text_rep)
            self.assertIn("ascii_graph", parsed_json)
            self.assertEqual(parsed_json["ascii_graph"], self.ascii_rep)

    def test_export_json_report_raises_exporter_error(self):
        self.anomaly_visualizer_mock.get_summary_metrics.side_effect = Exception(uuid.uuid4().hex)
        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(self.output_path)

    def test_export_html_report_success(self):
        m_open = mock_open()
        with patch("builtins.open", m_open):
            result = self.exporter.export_html_report(self.html_output_path)
            
            self.assertEqual(result, self.html_output_path)
            m_open.assert_called_once_with(self.html_output_path, "w", encoding="utf-8")
            
            handle = m_open()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            
            self.assertIn("<html>", written_data)
            self.assertIn(self.text_rep, written_data)
            self.assertIn(self.ascii_rep, written_data)

    def test_export_html_report_raises_exporter_error(self):
        self.anomaly_visualizer_mock.render_text.side_effect = Exception(uuid.uuid4().hex)
        with self.assertRaises(DigestExporterError):
            self.exporter.export_html_report(self.html_output_path)

    def test_export_stream_to_json_success(self):
        m_open = mock_open()
        with patch("builtins.open", m_open):
            result = self.exporter.export_stream_to_json(self.stream_id, self.output_path)
            
            self.assertEqual(result, self.output_path)
            self.stability_digest_mock.export_digest_stream.assert_called_once_with(self.stream_id)
            
            m_open.assert_called_once_with(self.output_path, "w", encoding="utf-8")
            handle = m_open()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)
            
            self.assertEqual(parsed_json, self.digest_data)

    def test_export_stream_to_json_raises_exporter_error(self):
        self.stability_digest_mock.export_digest_stream.side_effect = Exception(uuid.uuid4().hex)
        with self.assertRaises(DigestExporterError):
            self.exporter.export_stream_to_json(self.stream_id, self.output_path)

    def test_export_to_json_success(self):
        m_open = mock_open()
        with patch("builtins.open", m_open):
            result = self.exporter.export_to_json(self.output_path)
            
            self.assertEqual(result, self.output_path)
            m_open.assert_called_once_with(self.output_path, "w", encoding="utf-8")
            
            handle = m_open()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)
            
            self.assertEqual(parsed_json, self.digest_data)

    def test_export_to_json_empty_digest(self):
        exporter_no_digest = DigestExporter(anomaly_visualizer=None)
        m_open = mock_open()
        with patch("builtins.open", m_open):
            result = exporter_no_digest.export_to_json(self.output_path)
            self.assertEqual(result, self.output_path)
            
            handle = m_open()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)
            self.assertEqual(parsed_json, {})

    def test_export_to_json_raises_exporter_error(self):
        with patch("builtins.open", side_effect=PermissionError(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_json(self.output_path)

    def test_export_to_html_success(self):
        m_open = mock_open()
        with patch("builtins.open", m_open):
            result = self.exporter.export_to_html(self.html_output_path)
            
            self.assertEqual(result, self.html_output_path)
            m_open.assert_called_once_with(self.html_output_path, "w", encoding="utf-8")
            
            handle = m_open()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            
            self.assertIn("<html>", written_data)
            self.assertIn(json.dumps(self.digest_data), written_data)

    def test_export_to_html_raises_exporter_error(self):
        with patch("builtins.open", side_effect=PermissionError(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_html(self.html_output_path)


if __name__ == "__main__":
    unittest.main()