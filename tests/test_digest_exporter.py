import io
import json
import os
import random
import string
import tempfile
import unittest
from unittest.mock import MagicMock, patch

try:
    from skills.digest_exporter import DigestExporter, DigestExporterError
except ImportError:
    from digest_exporter import DigestExporter, DigestExporterError


def _generate_random_string(length=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def _generate_random_dict():
    return {
        _generate_random_string(6): _generate_random_string(10),
        _generate_random_string(5): random.randint(1, 1000),
    }


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _get_temp_filepath(self, extension=".txt"):
        filename = f"{_generate_random_string(10)}{extension}"
        return os.path.join(self.temp_dir.name, filename)

    def test_validate_structure_dict(self):
        exporter = DigestExporter()
        data_dict = _generate_random_dict()
        self.assertTrue(exporter.validate_structure(data_dict))

    def test_validate_structure_non_dict(self):
        exporter = DigestExporter()
        invalid_inputs = [
            _generate_random_string(8),
            random.randint(1, 100),
            [_generate_random_string(4)],
            None,
            3.14159,
        ]
        for item in invalid_inputs:
            self.assertFalse(
                exporter.validate_structure(item),
                msg=f"Expected False for input: {item}",
            )

    def test_export_json_report_success(self):
        mock_visualizer = MagicMock()
        random_metrics = _generate_random_dict()
        random_text = f"TEXT_{_generate_random_string(15)}"
        random_ascii = f"ASCII_{_generate_random_string(15)}"

        mock_visualizer.get_summary_metrics.return_value = random_metrics
        mock_visualizer.render_text.return_value = random_text
        mock_visualizer.render_ascii_correlation_graph.return_value = random_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        output_path = self._get_temp_filepath(".json")

        res_path = exporter.export_json_report(output_path)
        self.assertEqual(res_path, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["text_report"], random_text)
        self.assertEqual(data["ascii_graph"], random_ascii)
        for key, val in random_metrics.items():
            self.assertEqual(data.get(key), val)

    def test_export_json_report_non_dict_metrics(self):
        mock_visualizer = MagicMock()
        mock_visualizer.get_summary_metrics.return_value = _generate_random_string(10)
        mock_visualizer.render_text.return_value = _generate_random_string(8)
        mock_visualizer.render_ascii_correlation_graph.return_value = _generate_random_string(8)

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        output_path = self._get_temp_filepath(".json")

        res_path = exporter.export_json_report(output_path)
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("text_report", data)
        self.assertIn("ascii_graph", data)

    def test_export_json_report_error_wrapping(self):
        mock_visualizer = MagicMock()
        err_msg = f"VizError_{_generate_random_string(6)}"
        mock_visualizer.get_summary_metrics.side_effect = RuntimeError(err_msg)

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        output_path = self._get_temp_filepath(".json")

        with self.assertRaises(DigestExporterError) as ctx:
            exporter.export_json_report(output_path)
        self.assertIn(err_msg, str(ctx.exception))

    def test_export_json_report_direct_exporter_error_reraised(self):
        mock_visualizer = MagicMock()
        custom_err = DigestExporterError(f"Custom_{_generate_random_string(5)}")
        mock_visualizer.get_summary_metrics.side_effect = custom_err

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        output_path = self._get_temp_filepath(".json")

        with self.assertRaises(DigestExporterError) as ctx:
            exporter.export_json_report(output_path)
        self.assertIs(ctx.exception, custom_err)

    def test_export_html_report_success(self):
        mock_visualizer = MagicMock()
        random_metrics = _generate_random_dict()
        random_text = f"HTML_TEXT_{_generate_random_string(12)}"
        random_ascii = f"HTML_ASCII_{_generate_random_string(12)}"

        mock_visualizer.get_summary_metrics.return_value = random_metrics
        mock_visualizer.render_text.return_value = random_text
        mock_visualizer.render_ascii_correlation_graph.return_value = random_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        output_path = self._get_temp_filepath(".html")

        res_path = exporter.export_html_report(output_path)
        self.assertEqual(res_path, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        self.assertIn("<html>", html_content)
        self.assertIn(random_text, html_content)
        self.assertIn(random_ascii, html_content)
        self.assertIn(str(random_metrics), html_content)

    def test_export_html_report_error_wrapping(self):
        mock_visualizer = MagicMock()
        mock_visualizer.get_summary_metrics.side_effect = KeyError("Missing key")

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        output_path = self._get_temp_filepath(".html")

        with self.assertRaises(DigestExporterError):
            exporter.export_html_report(output_path)

    def test_export_markdown_report_success_with_visualizer(self):
        mock_visualizer = MagicMock()
        random_metrics = _generate_random_dict()
        random_text = f"MD_TEXT_{_generate_random_string(10)}"
        random_ascii = f"MD_ASCII_{_generate_random_string(10)}"

        mock_visualizer.get_summary_metrics.return_value = random_metrics
        mock_visualizer.render_text.return_value = random_text
        mock_visualizer.render_ascii_correlation_graph.return_value = random_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        output_path = self._get_temp_filepath(".md")

        res_path = exporter.export_markdown_report(output_path)
        self.assertEqual(res_path, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        self.assertIn("# Stability Digest Report", md_content)
        self.assertIn(random_text, md_content)
        self.assertIn(random_ascii, md_content)

    def test_export_markdown_report_without_visualizer(self):
        exporter = DigestExporter()
        output_path = self._get_temp_filepath(".md")

        res_path = exporter.export_markdown_report(output_path)
        self.assertEqual(res_path, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        self.assertIn("# Stability Digest Report", md_content)
        self.assertIn("## Metrics\n{}\n", md_content)

    def test_export_stream_to_json_success(self):
        mock_digest = MagicMock()
        stream_id = f"stream_{_generate_random_string(8)}"
        random_stream_data = _generate_random_dict()
        mock_digest.export_digest_stream.return_value = random_stream_data

        exporter = DigestExporter(stability_digest=mock_digest)
        output_path = self._get_temp_filepath(".json")

        res_path = exporter.export_stream_to_json(stream_id, output_path)
        self.assertEqual(res_path, output_path)
        mock_digest.export_digest_stream.assert_called_once_with(stream_id)

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data, random_stream_data)

    def test_export_stream_to_json_failure(self):
        mock_digest = MagicMock()
        stream_id = f"stream_{_generate_random_string(8)}"
        err_msg = f"StreamError_{_generate_random_string(5)}"
        mock_digest.export_digest_stream.side_effect = ValueError(err_msg)

        exporter = DigestExporter(stability_digest=mock_digest)
        output_path = self._get_temp_filepath(".json")

        with self.assertRaises(DigestExporterError) as ctx:
            exporter.export_stream_to_json(stream_id, output_path)
        self.assertIn(err_msg, str(ctx.exception))

    def test_export_to_json_adapter_with_digest_dict(self):
        mock_visualizer = MagicMock()
        random_digest_dict = _generate_random_dict()
        mock_visualizer.digest = random_digest_dict

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        output_path = self._get_temp_filepath(".json")

        res_path = exporter.export_to_json(output_path)
        self.assertEqual(res_path, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data, random_digest_dict)

    def test_export_to_json_adapter_without_visualizer(self):
        exporter = DigestExporter()
        output_path = self._get_temp_filepath(".json")

        res_path = exporter.export_to_json(output_path)
        self.assertEqual(res_path, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data, {})

    def test_export_to_html_adapter_with_digest_dict(self):
        mock_visualizer = MagicMock()
        random_digest_dict = _generate_random_dict()
        mock_visualizer.digest = random_digest_dict

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        output_path = self._get_temp_filepath(".html")

        res_path = exporter.export_to_html(output_path)
        self.assertEqual(res_path, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<html><body><pre>", content)
        self.assertIn(json.dumps(random_digest_dict), content)

    def test_export_to_html_adapter_without_visualizer(self):
        exporter = DigestExporter()
        output_path = self._get_temp_filepath(".html")

        res_path = exporter.export_to_html(output_path)
        self.assertEqual(res_path, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertEqual(content, "<html><body><pre>{}</pre></body></html>")

    def test_export_to_markdown_adapter_with_digest_dict(self):
        mock_visualizer = MagicMock()
        random_digest_dict = _generate_random_dict()
        mock_visualizer.digest = random_digest_dict

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        output_path = self._get_temp_filepath(".md")

        res_path = exporter.export_to_markdown(output_path)
        self.assertEqual(res_path, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertTrue(content.startswith("```json\n"))
        self.assertTrue(content.endswith("\n```"))
        self.assertIn(json.dumps(random_digest_dict, ensure_ascii=False, indent=4), content)

    def test_export_to_markdown_adapter_without_visualizer(self):
        exporter = DigestExporter()
        output_path = self._get_temp_filepath(".md")

        res_path = exporter.export_to_markdown(output_path)
        self.assertEqual(res_path, output_path)

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertEqual(content, "```json\n{}\n```")

    def test_io_file_error_handling(self):
        exporter = DigestExporter()
        invalid_path = os.path.join(self.temp_dir.name, "non_existent_folder", "file.json")

        with self.assertRaises(DigestExporterError):
            exporter.export_markdown_report(invalid_path)

        with self.assertRaises(DigestExporterError):
            exporter.export_to_json(invalid_path)

        with self.assertRaises(DigestExporterError):
            exporter.export_to_html(invalid_path)


if __name__ == "__main__":
    unittest.main()