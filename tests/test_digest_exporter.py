import unittest
from unittest.mock import MagicMock, patch
import json
import uuid
import random
import os
import io

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

    def tearDown(self):
        for path in [self.output_path, self.html_output_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_export_json_report_success(self):
        metric_key = uuid.uuid4().hex
        metric_val = random.randint(1, 1000)
        text_content = uuid.uuid4().hex
        ascii_content = uuid.uuid4().hex

        self.mock_visualizer.get_summary_metrics.return_value = {metric_key: metric_val}
        self.mock_visualizer.render_text.return_value = text_content
        self.mock_visualizer.render_ascii_correlation_graph.return_value = ascii_content

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_json_report(self.output_path)
            self.assertEqual(res_path, self.output_path)
            mock_file.assert_called_once_with(self.output_path, "w", encoding="utf-8")

    def test_export_json_report_raises_exporter_error(self):
        err_msg = uuid.uuid4().hex
        self.mock_visualizer.get_summary_metrics.side_effect = Exception(err_msg)

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_json_report(self.output_path)
        self.assertIn(err_msg, str(ctx.exception))

    def test_export_html_report_success(self):
        text_content = uuid.uuid4().hex
        ascii_content = uuid.uuid4().hex
        metric_str = uuid.uuid4().hex

        self.mock_visualizer.get_summary_metrics.return_value = metric_str
        self.mock_visualizer.render_text.return_value = text_content
        self.mock_visualizer.render_ascii_correlation_graph.return_value = ascii_content

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_html_report(self.html_output_path)
            self.assertEqual(res_path, self.html_output_path)
            mock_file.assert_called_once_with(self.html_output_path, "w", encoding="utf-8")

    def test_export_html_report_raises_exporter_error(self):
        err_msg = uuid.uuid4().hex
        self.mock_visualizer.get_summary_metrics.side_effect = RuntimeError(err_msg)

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_html_report(self.html_output_path)
        self.assertIn(err_msg, str(ctx.exception))

    def test_export_stream_to_json_success(self):
        stream_data = {uuid.uuid4().hex: random.randint(1, 500)}
        self.mock_digest.export_digest_stream.return_value = stream_data

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_stream_to_json(self.stream_id, self.output_path)
            self.assertEqual(res_path, self.output_path)
            self.mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)

    def test_export_stream_to_json_raises_exporter_error(self):
        err_msg = uuid.uuid4().hex
        self.mock_digest.export_digest_stream.side_effect = ValueError(err_msg)

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_stream_to_json(self.stream_id, self.output_path)
        self.assertIn(err_msg, str(ctx.exception))

    def test_export_to_json_adapter_with_dict(self):
        digest_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_visualizer.digest = digest_data

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_to_json(self.output_path)
            self.assertEqual(res_path, self.output_path)

    def test_export_to_json_adapter_without_dict(self):
        self.mock_visualizer.digest = uuid.uuid4().hex

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_to_json(self.output_path)
            self.assertEqual(res_path, self.output_path)

    def test_export_to_json_adapter_raises_error(self):
        with patch("builtins.open", side_effect=PermissionError(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_json(self.output_path)

    def test_export_to_html_adapter_success(self):
        digest_data = {uuid.uuid4().hex: random.randint(10, 99)}
        self.mock_visualizer.digest = digest_data

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_to_html(self.html_output_path)
            self.assertEqual(res_path, self.html_output_path)

    def test_export_to_html_adapter_raises_error(self):
        self.mock_visualizer.digest = {uuid.uuid4().hex: uuid.uuid4().hex}
        with patch("builtins.open", side_effect=IOError(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_html(self.html_output_path)

    def test_pre_existing_digest_exporter_error_passthrough(self):
        custom_err = DigestExporterError(uuid.uuid4().hex)
        self.mock_visualizer.get_summary_metrics.side_effect = custom_err

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_json_report(self.output_path)
        self.assertEqual(str(ctx.exception), str(custom_err))


if __name__ == "__main__":
    unittest.main()