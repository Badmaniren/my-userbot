import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import json
import io
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.output_path = f"{uuid.uuid4().hex}.json"
        self.html_output_path = f"{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex
        self.random_metric_key = uuid.uuid4().hex
        self.random_metric_value = random.randint(100, 9999)
        self.random_text = f"report_text_{uuid.uuid4().hex}"
        self.random_ascii = f"ascii_graph_{uuid.uuid4().hex}"

    def test_export_json_report_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        mock_visualizer.get_summary_metrics.return_value = {self.random_metric_key: self.random_metric_value}
        mock_visualizer.render_text.return_value = self.random_text
        mock_visualizer.render_ascii_correlation_graph.return_value = self.random_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        m_open = mock_open()
        with patch("builtins.open", m_open):
            result_path = exporter.export_json_report(self.output_path)

        self.assertEqual(result_path, self.output_path)
        m_open.assert_called_once_with(self.output_path, "w", encoding="utf-8")

        handle = m_open()
        written_data = "".join(call.args[0] for call in handle.write.call_args_list)
        parsed_data = json.loads(written_data)

        self.assertEqual(parsed_data.get(self.random_metric_key), self.random_metric_value)
        self.assertEqual(parsed_data.get("text_report"), self.random_text)
        self.assertEqual(parsed_data.get("ascii_graph"), self.random_ascii)

    def test_export_html_report_success(self):
        mock_digest = unittest.mock.MagicMock()
        mock_digest.get_summary_metrics.return_value = {self.random_metric_key: self.random_metric_value}

        exporter = DigestExporter(stability_digest=mock_digest)

        m_open = mock_open()
        with patch("builtins.open", m_open):
            result_path = exporter.export_html_report(self.html_output_path)

        self.assertEqual(result_path, self.html_output_path)
        m_open.assert_called_once_with(self.html_output_path, "w", encoding="utf-8")

        handle = m_open()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)

        self.assertIn("<html>", written_content)
        self.assertIn(self.random_metric_key, written_content)
        self.assertIn(str(self.random_metric_value), written_content)

    def test_export_stream_to_json_success(self):
        mock_digest = unittest.mock.MagicMock()
        expected_stream_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_digest.export_digest_stream.return_value = expected_stream_data

        exporter = DigestExporter(stability_digest=mock_digest)

        m_open = mock_open()
        with patch("builtins.open", m_open):
            result_path = exporter.export_stream_to_json(self.stream_id, self.output_path)

        self.assertEqual(result_path, self.output_path)
        mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)

        handle = m_open()
        written_data = "".join(call.args[0] for call in handle.write.call_args_list)
        parsed_data = json.loads(written_data)
        self.assertEqual(parsed_data, expected_stream_data)

    def test_export_stream_to_json_error(self):
        exporter = DigestExporter(stability_digest=None)
        with self.assertRaises(DigestExporterError):
            exporter.export_stream_to_json(self.stream_id, self.output_path)

    def test_export_to_json_adapter_success(self):
        mock_digest = unittest.mock.MagicMock()
        inner_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_digest.digest = inner_dict

        exporter = DigestExporter(stability_digest=mock_digest)

        m_open = mock_open()
        with patch("builtins.open", m_open):
            result_path = exporter.export_to_json(self.output_path)

        self.assertEqual(result_path, self.output_path)
        handle = m_open()
        written_data = "".join(call.args[0] for call in handle.write.call_args_list)
        parsed_data = json.loads(written_data)
        self.assertEqual(parsed_data, inner_dict)

    def test_export_to_html_adapter_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        inner_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_visualizer.digest = inner_dict

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        m_open = mock_open()
        with patch("builtins.open", m_open):
            result_path = exporter.export_to_html(self.html_output_path)

        self.assertEqual(result_path, self.html_output_path)
        handle = m_open()
        written_content = "".join(call.args[0] for call in handle.write.call_args_list)
        self.assertIn("<html><body><pre>", written_content)
        self.assertIn(json.dumps(inner_dict), written_content)

    def test_export_json_report_exception_handling(self):
        exporter = DigestExporter()
        with patch("builtins.open", side_effect=IOError(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                exporter.export_json_report(self.output_path)


if __name__ == "__main__":
    unittest.main()