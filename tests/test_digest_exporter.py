import unittest
from unittest.mock import patch, mock_open, MagicMock
import uuid
import random
import io
import json

from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.output_path = f"{uuid.uuid4().hex}.json"
        self.html_output_path = f"{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex

        self.mock_visualizer = MagicMock()
        self.mock_digest = MagicMock()

        self.exporter = DigestExporter(
            stability_digest=self.mock_digest,
            anomaly_visualizer=self.mock_visualizer
        )

    def test_init_default_values(self):
        exporter = DigestExporter()
        self.assertIsNone(exporter.digest)
        self.assertIsNone(exporter.visualizer)

    def test_export_json_report_success(self):
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        text_content = uuid.uuid4().hex
        ascii_content = uuid.uuid4().hex

        self.mock_visualizer.get_summary_metrics.return_value = {random_key: random_val}
        self.mock_visualizer.render_text.return_value = text_content
        self.mock_visualizer.render_ascii_correlation_graph.return_value = ascii_content

        m_open = mock_open()
        with patch('builtins.open', m_open):
            result = self.exporter.export_json_report(self.output_path)

        self.assertEqual(result, self.output_path)
        m_open.assert_called_once_with(self.output_path, 'w', encoding='utf-8')

    def test_export_json_report_none_visualizer(self):
        exporter = DigestExporter(stability_digest=self.mock_digest, anomaly_visualizer=None)
        m_open = mock_open()
        with patch('builtins.open', m_open):
            result = exporter.export_json_report(self.output_path)
        self.assertEqual(result, self.output_path)

    def test_export_json_report_exception_handling(self):
        self.mock_visualizer.get_summary_metrics.side_effect = Exception(uuid.uuid4().hex)
        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(self.output_path)

    def test_export_html_report_success(self):
        metrics_val = uuid.uuid4().hex
        text_val = uuid.uuid4().hex
        ascii_val = uuid.uuid4().hex

        self.mock_visualizer.get_summary_metrics.return_value = metrics_val
        self.mock_visualizer.render_text.return_value = text_val
        self.mock_visualizer.render_ascii_correlation_graph.return_value = ascii_val

        m_open = mock_open()
        with patch('builtins.open', m_open):
            result = self.exporter.export_html_report(self.html_output_path)

        self.assertEqual(result, self.html_output_path)
        m_open.assert_called_once_with(self.html_output_path, 'w', encoding='utf-8')

    def test_export_html_report_exception(self):
        self.mock_visualizer.render_text.side_effect = Exception(uuid.uuid4().hex)
        with self.assertRaises(DigestExporterError):
            self.exporter.export_html_report(self.html_output_path)

    def test_export_stream_to_json_success(self):
        stream_key = uuid.uuid4().hex
        stream_val = uuid.uuid4().hex
        self.mock_digest.export_digest_stream.return_value = {stream_key: stream_val}

        m_open = mock_open()
        with patch('builtins.open', m_open):
            result = self.exporter.export_stream_to_json(self.stream_id, self.output_path)

        self.assertEqual(result, self.output_path)
        self.mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)

    def test_export_stream_to_json_no_digest(self):
        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=self.mock_visualizer)
        m_open = mock_open()
        with patch('builtins.open', m_open):
            result = exporter.export_stream_to_json(self.stream_id, self.output_path)
        self.assertEqual(result, self.output_path)

    def test_export_stream_to_json_exception(self):
        self.mock_digest.export_digest_stream.side_effect = Exception(uuid.uuid4().hex)
        with self.assertRaises(DigestExporterError):
            self.exporter.export_stream_to_json(self.stream_id, self.output_path)

    def test_export_to_json_via_visualizer(self):
        data_key = uuid.uuid4().hex
        data_val = uuid.uuid4().hex
        self.mock_visualizer.digest = {data_key: data_val}

        m_open = mock_open()
        with patch('builtins.open', m_open):
            result = self.exporter.export_to_json(self.output_path)

        self.assertEqual(result, self.output_path)

    def test_export_to_json_via_digest(self):
        exporter = DigestExporter(stability_digest=self.mock_digest, anomaly_visualizer=None)
        data_key = uuid.uuid4().hex
        data_val = uuid.uuid4().hex
        self.mock_digest.digest = {data_key: data_val}

        m_open = mock_open()
        with patch('builtins.open', m_open):
            result = exporter.export_to_json(self.output_path)

        self.assertEqual(result, self.output_path)

    def test_export_to_json_fallback(self):
        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=None)
        m_open = mock_open()
        with patch('builtins.open', m_open):
            result = exporter.export_to_json(self.output_path)
        self.assertEqual(result, self.output_path)

    def test_export_to_json_exception(self):
        with patch('builtins.open', side_effect=Exception(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_json(self.output_path)

    def test_export_to_html_via_visualizer(self):
        data_key = uuid.uuid4().hex
        data_val = uuid.uuid4().hex
        self.mock_visualizer.digest = {data_key: data_val}

        m_open = mock_open()
        with patch('builtins.open', m_open):
            result = self.exporter.export_to_html(self.html_output_path)

        self.assertEqual(result, self.html_output_path)

    def test_export_to_html_via_digest(self):
        exporter = DigestExporter(stability_digest=self.mock_digest, anomaly_visualizer=None)
        data_key = uuid.uuid4().hex
        data_val = uuid.uuid4().hex
        self.mock_digest.digest = {data_key: data_val}

        m_open = mock_open()
        with patch('builtins.open', m_open):
            result = self.exporter.export_to_html(self.html_output_path)

        self.assertEqual(result, self.html_output_path)

    def test_export_to_html_fallback(self):
        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=None)
        m_open = mock_open()
        with patch('builtins.open', m_open):
            result = exporter.export_to_html(self.html_output_path)
        self.assertEqual(result, self.html_output_path)

    def test_export_to_html_exception(self):
        with patch('builtins.open', side_effect=Exception(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_html(self.html_output_path)

    def test_digest_exporter_error_passthrough(self):
        original_error = DigestExporterError(uuid.uuid4().hex)
        self.mock_visualizer.get_summary_metrics.side_effect = original_error
        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_json_report(self.output_path)
        self.assertEqual(ctx.exception, original_error)


if __name__ == '__main__':
    unittest.main()