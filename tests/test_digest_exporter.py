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
        self.exporter = DigestExporter()

    def test_export_json_report_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(100, 999)
        rand_text = uuid.uuid4().hex
        rand_ascii = uuid.uuid4().hex

        mock_visualizer.get_summary_metrics.return_value = {rand_metric_key: rand_metric_val}
        mock_visualizer.render_text.return_value = rand_text
        mock_visualizer.render_ascii_correlation_graph.return_value = rand_ascii

        self.exporter.visualizer = mock_visualizer

        with patch("builtins.open", mock_open()) as mocked_file:
            result = self.exporter.export_json_report(self.output_path)
            self.assertEqual(result, self.output_path)
            mocked_file.assert_called_once_with(self.output_path, "w", encoding="utf-8")

    def test_export_json_report_failure(self):
        mock_visualizer = unittest.mock.MagicMock()
        mock_visualizer.get_summary_metrics.side_effect = Exception(uuid.uuid4().hex)
        self.exporter.visualizer = mock_visualizer

        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(self.output_path)

    def test_export_html_report_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        rand_metric = uuid.uuid4().hex
        mock_visualizer.get_summary_metrics.return_value = rand_metric
        mock_visualizer.render_text.return_value = uuid.uuid4().hex
        mock_visualizer.render_ascii_correlation_graph.return_value = uuid.uuid4().hex

        self.exporter.visualizer = mock_visualizer

        with patch("builtins.open", mock_open()) as mocked_file:
            result = self.exporter.export_html_report(self.html_output_path)
            self.assertEqual(result, self.html_output_path)
            mocked_file.assert_called_once_with(self.html_output_path, "w", encoding="utf-8")

    def test_export_html_report_failure(self):
        mock_visualizer = unittest.mock.MagicMock()
        mock_visualizer.get_summary_metrics.side_effect = Exception(uuid.uuid4().hex)
        self.exporter.visualizer = mock_visualizer

        with self.assertRaises(DigestExporterError):
            self.exporter.export_html_report(self.html_output_path)

    def test_export_stream_to_json_success(self):
        mock_digest = unittest.mock.MagicMock()
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        mock_digest.export_digest_stream.return_value = {rand_key: rand_val}
        self.exporter.digest = mock_digest

        with patch("builtins.open", mock_open()) as mocked_file:
            result = self.exporter.export_stream_to_json(self.stream_id, self.output_path)
            self.assertEqual(result, self.output_path)
            mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)

    def test_export_stream_to_json_failure(self):
        mock_digest = unittest.mock.MagicMock()
        mock_digest.export_digest_stream.side_effect = Exception(uuid.uuid4().hex)
        self.exporter.digest = mock_digest

        with self.assertRaises(DigestExporterError):
            self.exporter.export_stream_to_json(self.stream_id, self.output_path)

    def test_export_to_json_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        rand_key = uuid.uuid4().hex
        rand_val = random.randint(1, 100)
        mock_visualizer.digest = {rand_key: rand_val}
        self.exporter.visualizer = mock_visualizer

        with patch("builtins.open", mock_open()) as mocked_file:
            result = self.exporter.export_to_json(self.output_path)
            self.assertEqual(result, self.output_path)

    def test_export_to_json_no_digest_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        del mock_visualizer.digest
        self.exporter.visualizer = mock_visualizer

        with patch("builtins.open", mock_open()) as mocked_file:
            result = self.exporter.export_to_json(self.output_path)
            self.assertEqual(result, self.output_path)

    def test_export_to_html_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        mock_visualizer.digest = {rand_key: rand_val}
        self.exporter.visualizer = mock_visualizer

        with patch("builtins.open", mock_open()) as mocked_file:
            result = self.exporter.export_to_html(self.html_output_path)
            self.assertEqual(result, self.html_output_path)

    def test_export_to_html_failure(self):
        mock_visualizer = unittest.mock.MagicMock()
        type(mock_visualizer).digest = unittest.mock.PropertyMock(side_effect=Exception(uuid.uuid4().hex))
        self.exporter.visualizer = mock_visualizer

        with self.assertRaises(DigestExporterError):
            self.exporter.export_to_html(self.html_output_path)


if __name__ == "__main__":
    unittest.main()