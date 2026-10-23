import unittest
from unittest.mock import patch, mock_open, MagicMock
import uuid
import random
import json
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.output_path = f"{uuid.uuid4().hex}.json"
        self.html_output_path = f"{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex
        self.metrics_key = uuid.uuid4().hex
        self.metrics_val = random.randint(100, 999)
        self.text_content = uuid.uuid4().hex
        self.ascii_content = uuid.uuid4().hex

    def test_export_json_report_success(self):
        mock_visualizer = MagicMock()
        mock_visualizer.get_summary_metrics.return_value = {self.metrics_key: self.metrics_val}
        mock_visualizer.render_text.return_value = self.text_content
        mock_visualizer.render_ascii_correlation_graph.return_value = self.ascii_content

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            res_path = exporter.export_json_report(self.output_path)
            self.assertEqual(res_path, self.output_path)
            mocked_file.assert_called_once_with(self.output_path, "w", encoding="utf-8")

    def test_export_json_report_handles_missing_methods(self):
        exporter = DigestExporter(anomaly_visualizer=None)

        with patch("builtins.open", mock_open()) as mocked_file:
            res_path = exporter.export_json_report(self.output_path)
            self.assertEqual(res_path, self.output_path)

    def test_export_json_report_raises_exporter_error(self):
        mock_visualizer = MagicMock()
        mock_visualizer.get_summary_metrics.side_effect = Exception(uuid.uuid4().hex)

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with self.assertRaises(DigestExporterError):
            exporter.export_json_report(self.output_path)

    def test_export_html_report_success(self):
        mock_visualizer = MagicMock()
        mock_visualizer.get_summary_metrics.return_value = {self.metrics_key: self.metrics_val}
        mock_visualizer.render_text.return_value = self.text_content
        mock_visualizer.render_ascii_correlation_graph.return_value = self.ascii_content

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            res_path = exporter.export_html_report(self.html_output_path)
            self.assertEqual(res_path, self.html_output_path)
            mocked_file.assert_called_once_with(self.html_output_path, "w", encoding="utf-8")

    def test_export_html_report_raises_exporter_error(self):
        mock_visualizer = MagicMock()
        mock_visualizer.render_text.side_effect = RuntimeError(uuid.uuid4().hex)

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with self.assertRaises(DigestExporterError):
            exporter.export_html_report(self.html_output_path)

    def test_export_stream_to_json_success(self):
        mock_digest = MagicMock()
        stream_data = {uuid.uuid4().hex: random.randint(1, 100)}
        mock_digest.export_digest_stream.return_value = stream_data

        exporter = DigestExporter(stability_digest=mock_digest)

        with patch("builtins.open", mock_open()) as mocked_file:
            res_path = exporter.export_stream_to_json(self.stream_id, self.output_path)
            self.assertEqual(res_path, self.output_path)
            mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)

    def test_export_stream_to_json_raises_exporter_error(self):
        mock_digest = MagicMock()
        mock_digest.export_digest_stream.side_effect = TypeError(uuid.uuid4().hex)

        exporter = DigestExporter(stability_digest=mock_digest)

        with self.assertRaises(DigestExporterError):
            exporter.export_stream_to_json(self.stream_id, self.output_path)

    def test_export_to_json_adapter_with_digest_dict(self):
        mock_visualizer = MagicMock()
        digest_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_visualizer.digest = digest_dict

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            res_path = exporter.export_to_json(self.output_path)
            self.assertEqual(res_path, self.output_path)

    def test_export_to_json_adapter_with_metrics(self):
        mock_visualizer = MagicMock()
        del mock_visualizer.digest
        mock_visualizer.get_summary_metrics.return_value = {uuid.uuid4().hex: uuid.uuid4().hex}

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            res_path = exporter.export_to_json(self.output_path)
            self.assertEqual(res_path, self.output_path)

    def test_export_to_json_adapter_raises_exporter_error(self):
        mock_visualizer = MagicMock()
        type(mock_visualizer).digest = property(lambda self: (_ for _ in ()).throw(Exception(uuid.uuid4().hex)))

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with self.assertRaises(DigestExporterError):
            exporter.export_to_json(self.output_path)

    def test_export_to_html_adapter_success(self):
        mock_visualizer = MagicMock()
        mock_visualizer.digest = {uuid.uuid4().hex: random.randint(1, 500)}

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            res_path = exporter.export_to_html(self.html_output_path)
            self.assertEqual(res_path, self.html_output_path)

    def test_export_to_html_adapter_raises_exporter_error(self):
        mock_visualizer = MagicMock()
        type(mock_visualizer).digest = property(lambda self: (_ for _ in ()).throw(KeyError(uuid.uuid4().hex)))

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with self.assertRaises(DigestExporterError):
            exporter.export_to_html(self.html_output_path)


if __name__ == "__main__":
    unittest.main()