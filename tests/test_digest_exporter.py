import unittest
from unittest.mock import MagicMock, patch
import json
import uuid
import random
import os
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporterInquisition(unittest.TestCase):
    """Инквизиционные юнит-тесты для модуля DigestExporter."""

    def setUp(self):
        self.output_path = f"report_{uuid.uuid4().hex}.json"
        self.html_output_path = f"report_{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex
        
        self.mock_visualizer = MagicMock()
        self.mock_digest = MagicMock()
        
        self.exporter = DigestExporter(
            stability_digest=self.mock_digest,
            anomaly_visualizer=self.mock_visualizer
        )

    def tearDown(self):
        for path in [self.output_path, self.html_output_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_export_json_report_success(self):
        expected_metric_key = uuid.uuid4().hex
        expected_metric_val = random.randint(100, 999)
        expected_text = uuid.uuid4().hex
        expected_ascii = uuid.uuid4().hex

        self.mock_visualizer.get_summary_metrics.return_value = {expected_metric_key: expected_metric_val}
        self.mock_visualizer.render_text.return_value = expected_text
        self.mock_visualizer.render_ascii_correlation_graph.return_value = expected_ascii

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_json_report(self.output_path)
            self.assertEqual(res_path, self.output_path)
            mock_file.assert_called_once_with(self.output_path, "w", encoding="utf-8")

    def test_export_json_report_raises_exporter_error(self):
        self.mock_visualizer.get_summary_metrics.side_effect = RuntimeError(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(self.output_path)

    def test_export_html_report_success(self):
        expected_text = uuid.uuid4().hex
        self.mock_visualizer.get_summary_metrics.return_value = {"score": random.random()}
        self.mock_visualizer.render_text.return_value = expected_text
        self.mock_visualizer.render_ascii_correlation_graph.return_value = uuid.uuid4().hex

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_html_report(self.html_output_path)
            self.assertEqual(res_path, self.html_output_path)
            mock_file.assert_called_once_with(self.html_output_path, "w", encoding="utf-8")

    def test_export_html_report_raises_exporter_error(self):
        self.mock_visualizer.render_text.side_effect = ValueError(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_html_report(self.html_output_path)

    def test_export_stream_to_json_success(self):
        expected_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_digest.export_digest_stream.return_value = expected_data

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_stream_to_json(self.stream_id, self.output_path)
            self.assertEqual(res_path, self.output_path)
            self.mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)

    def test_export_stream_to_json_raises_exporter_error(self):
        self.mock_digest.export_digest_stream.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_stream_to_json(self.stream_id, self.output_path)

    def test_export_to_json_adapter_success(self):
        key = uuid.uuid4().hex
        val = uuid.uuid4().hex
        self.mock_visualizer.digest = {key: val}

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_to_json(self.output_path)
            self.assertEqual(res_path, self.output_path)

    def test_export_to_json_adapter_empty_fallback(self):
        self.exporter.visualizer = None

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_to_json(self.output_path)
            self.assertEqual(res_path, self.output_path)

    def test_export_to_html_adapter_success(self):
        key = uuid.uuid4().hex
        val = uuid.uuid4().hex
        self.mock_visualizer.digest = {key: val}

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_to_html(self.html_output_path)
            self.assertEqual(res_path, self.html_output_path)

    def test_export_to_html_adapter_exception_wrapping(self):
        with patch("builtins.open", side_effect=PermissionError(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_html(self.html_output_path)


if __name__ == "__main__":
    unittest.main()