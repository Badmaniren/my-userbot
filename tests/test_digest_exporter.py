import unittest
from unittest.mock import MagicMock, patch
import json
import uuid
import random
import io
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.random_path = f"{uuid.uuid4().hex}.json"
        self.random_html_path = f"{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex

        self.mock_visualizer = MagicMock()
        self.mock_digest = MagicMock()

        self.exporter = DigestExporter(
            stability_digest=self.mock_digest,
            anomaly_visualizer=self.mock_visualizer
        )

    def test_export_json_report_success(self):
        metric_key = uuid.uuid4().hex
        metric_val = random.randint(1, 1000)
        text_content = uuid.uuid4().hex
        ascii_content = uuid.uuid4().hex

        self.mock_visualizer.get_summary_metrics.return_value = {metric_key: metric_val}
        self.mock_visualizer.render_text.return_value = text_content
        self.mock_visualizer.render_ascii_correlation_graph.return_value = ascii_content

        mock_file = MagicMock()
        with patch('builtins.open', return_value=mock_file) as mock_open:
            result_path = self.exporter.export_json_report(self.random_path)

            mock_open.assert_called_once_with(self.random_path, 'w', encoding='utf-8')
            self.assertEqual(result_path, self.random_path)

    def test_export_json_report_metrics_not_dict(self):
        self.mock_visualizer.get_summary_metrics.return_value = uuid.uuid4().hex
        self.mock_visualizer.render_text.return_value = uuid.uuid4().hex
        self.mock_visualizer.render_ascii_correlation_graph.return_value = uuid.uuid4().hex

        mock_file = MagicMock()
        with patch('builtins.open', return_value=mock_file):
            result_path = self.exporter.export_json_report(self.random_path)
            self.assertEqual(result_path, self.random_path)

    def test_export_json_report_raises_error(self):
        self.mock_visualizer.get_summary_metrics.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(self.random_path)

    def test_export_html_report_success(self):
        metric_key = uuid.uuid4().hex
        self.mock_visualizer.get_summary_metrics.return_value = {metric_key: random.randint(10, 50)}
        self.mock_visualizer.render_text.return_value = uuid.uuid4().hex
        self.mock_visualizer.render_ascii_correlation_graph.return_value = uuid.uuid4().hex

        mock_file = MagicMock()
        with patch('builtins.open', return_value=mock_file) as mock_open:
            result_path = self.exporter.export_html_report(self.random_html_path)

            mock_open.assert_called_once_with(self.random_html_path, 'w', encoding='utf-8')
            self.assertEqual(result_path, self.random_html_path)

    def test_export_html_report_raises_error(self):
        self.mock_visualizer.render_text.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_html_report(self.random_html_path)

    def test_export_stream_to_json_success(self):
        stream_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_digest.export_digest_stream.return_value = stream_payload

        mock_file = MagicMock()
        with patch('builtins.open', return_value=mock_file) as mock_open:
            result_path = self.exporter.export_stream_to_json(self.stream_id, self.random_path)

            self.mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)
            mock_open.assert_called_once_with(self.random_path, 'w', encoding='utf-8')
            self.assertEqual(result_path, self.random_path)

    def test_export_stream_to_json_raises_error(self):
        self.mock_digest.export_digest_stream.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_stream_to_json(self.stream_id, self.random_path)

    def test_export_to_json_adapter_success(self):
        digest_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.exporter.visualizer.digest = digest_dict

        mock_file = MagicMock()
        with patch('builtins.open', return_value=mock_file) as mock_open:
            result_path = self.exporter.export_to_json(self.random_path)

            mock_open.assert_called_once_with(self.random_path, 'w', encoding='utf-8')
            self.assertEqual(result_path, self.random_path)

    def test_export_to_json_adapter_empty_digest(self):
        self.exporter.visualizer = None

        mock_file = MagicMock()
        with patch('builtins.open', return_value=mock_file):
            result_path = self.exporter.export_to_json(self.random_path)
            self.assertEqual(result_path, self.random_path)

    def test_export_to_json_adapter_raises_error(self):
        with patch('builtins.open', side_effect=PermissionError(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_json(self.random_path)

    def test_export_to_html_adapter_success(self):
        digest_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.exporter.visualizer.digest = digest_dict

        mock_file = MagicMock()
        with patch('builtins.open', return_value=mock_file) as mock_open:
            result_path = self.exporter.export_to_html(self.random_html_path)

            mock_open.assert_called_once_with(self.random_html_path, 'w', encoding='utf-8')
            self.assertEqual(result_path, self.random_html_path)

    def test_export_to_html_adapter_no_visualizer(self):
        self.exporter.visualizer = None

        mock_file = MagicMock()
        with patch('builtins.open', return_value=mock_file):
            result_path = self.exporter.export_to_html(self.random_html_path)
            self.assertEqual(result_path, self.random_html_path)

    def test_export_to_html_adapter_raises_error(self):
        self.exporter.visualizer = MagicMock()
        del self.exporter.visualizer.digest

        with patch('builtins.open', side_effect=OSError(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_html(self.random_html_path)


if __name__ == '__main__':
    unittest.main()