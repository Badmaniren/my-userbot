import json
import os
import random
import string
import tempfile
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _get_random_str(self, length=12):
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def _get_random_path(self, extension="file"):
        filename = f"{uuid.uuid4().hex}_{self._get_random_str(6)}.{extension}"
        return os.path.join(self.tmp_dir.name, filename)

    def test_export_json_report_success(self):
        mock_vis = MagicMock()
        metric_key = f"key_{self._get_random_str()}"
        metric_val = random.randint(100, 9999)
        summary_metrics = {metric_key: metric_val}
        text_rep = f"text_{self._get_random_str()}"
        ascii_graph = f"ascii_{self._get_random_str()}"

        mock_vis.get_summary_metrics.return_value = summary_metrics
        mock_vis.render_text.return_value = text_rep
        mock_vis.render_ascii_correlation_graph.return_value = ascii_graph

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = self._get_random_path("json")

        result_path = exporter.export_json_report(out_path)

        self.assertEqual(result_path, out_path)
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get(metric_key), metric_val)
        self.assertEqual(data.get("text_report"), text_rep)
        self.assertEqual(data.get("ascii_graph"), ascii_graph)

    def test_export_json_report_non_dict_metrics(self):
        mock_vis = MagicMock()
        mock_vis.get_summary_metrics.return_value = [self._get_random_str()]
        text_rep = f"text_{self._get_random_str()}"
        ascii_graph = f"ascii_{self._get_random_str()}"

        mock_vis.render_text.return_value = text_rep
        mock_vis.render_ascii_correlation_graph.return_value = ascii_graph

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = self._get_random_path("json")

        exporter.export_json_report(out_path)

        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("text_report"), text_rep)
        self.assertEqual(data.get("ascii_graph"), ascii_graph)

    def test_export_json_report_raises_exporter_error_on_exception(self):
        mock_vis = MagicMock()
        error_msg = f"Error_{self._get_random_str()}"
        mock_vis.get_summary_metrics.side_effect = Exception(error_msg)

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = self._get_random_path("json")

        with self.assertRaises(DigestExporterError) as ctx:
            exporter.export_json_report(out_path)

        self.assertIn(error_msg, str(ctx.exception))

    def test_export_html_report_success(self):
        mock_vis = MagicMock()
        metric_key = f"m_{self._get_random_str()}"
        metric_val = self._get_random_str()
        summary_metrics = {metric_key: metric_val}
        text_rep = f"text_{self._get_random_str()}"
        ascii_graph = f"ascii_{self._get_random_str()}"

        mock_vis.get_summary_metrics.return_value = summary_metrics
        mock_vis.render_text.return_value = text_rep
        mock_vis.render_ascii_correlation_graph.return_value = ascii_graph

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = self._get_random_path("html")

        result_path = exporter.export_html_report(out_path)

        self.assertEqual(result_path, out_path)
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(text_rep, content)
        self.assertIn(ascii_graph, content)
        self.assertIn(metric_key, content)

    def test_export_html_report_error_handling(self):
        mock_vis = MagicMock()
        mock_vis.render_text.side_effect = RuntimeError(f"Fail_{self._get_random_str()}")

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = self._get_random_path("html")

        with self.assertRaises(DigestExporterError):
            exporter.export_html_report(out_path)

    def test_export_markdown_report_success(self):
        mock_vis = MagicMock()
        metric_key = f"m_{self._get_random_str()}"
        metric_val = self._get_random_str()
        summary_metrics = {metric_key: metric_val}
        text_rep = f"text_{self._get_random_str()}"
        ascii_graph = f"ascii_{self._get_random_str()}"

        mock_vis.get_summary_metrics.return_value = summary_metrics
        mock_vis.render_text.return_value = text_rep
        mock_vis.render_ascii_correlation_graph.return_value = ascii_graph

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = self._get_random_path("md")

        result_path = exporter.export_markdown_report(out_path)

        self.assertEqual(result_path, out_path)
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("# Stability Digest Report", content)
        self.assertIn(text_rep, content)
        self.assertIn(ascii_graph, content)
        self.assertIn(metric_key, content)

    def test_export_markdown_report_error_handling(self):
        mock_vis = MagicMock()
        mock_vis.render_text.side_effect = RuntimeError(f"Fail_{self._get_random_str()}")

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = self._get_random_path("md")

        with self.assertRaises(DigestExporterError):
            exporter.export_markdown_report(out_path)

    def test_export_to_markdown_adapter_with_valid_digest(self):
        mock_vis = MagicMock()
        key = f"k_{self._get_random_str()}"
        val = self._get_random_str()
        mock_vis.digest = {key: val}

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = self._get_random_path("md")

        result = exporter.export_to_markdown(out_path)

        self.assertEqual(result, out_path)
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("# Security Audit Digest Report", content)
        self.assertIn(key, content)
        self.assertIn(val, content)

    def test_export_to_markdown_error_handling(self):
        exporter = DigestExporter(anomaly_visualizer=None)
        invalid_path = os.path.join(self.tmp_dir.name, "non_existent_dir", "out.md")

        with self.assertRaises(DigestExporterError):
            exporter.export_to_markdown(invalid_path)

    def test_export_stream_to_json_success(self):
        mock_digest = MagicMock()
        stream_id = f"stream_{self._get_random_str()}"
        data_key = f"data_{self._get_random_str()}"
        data_val = random.randint(10, 1000)
        expected_stream_data = {data_key: data_val}

        mock_digest.export_digest_stream.return_value = expected_stream_data

        exporter = DigestExporter(stability_digest=mock_digest)
        out_path = self._get_random_path("json")

        result_path = exporter.export_stream_to_json(stream_id, out_path)

        self.assertEqual(result_path, out_path)
        mock_digest.export_digest_stream.assert_called_once_with(stream_id)

        with open(out_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, expected_stream_data)

    def test_export_stream_to_json_error_handling(self):
        mock_digest = MagicMock()
        stream_id = f"stream_{self._get_random_str()}"
        mock_digest.export_digest_stream.side_effect = KeyError(f"Missing_{self._get_random_str()}")

        exporter = DigestExporter(stability_digest=mock_digest)
        out_path = self._get_random_path("json")

        with self.assertRaises(DigestExporterError):
            exporter.export_stream_to_json(stream_id, out_path)

    def test_export_to_json_adapter_with_valid_digest(self):
        mock_vis = MagicMock()
        key = f"key_{self._get_random_str()}"
        val = self._get_random_str()
        mock_vis.digest = {key: val}

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = self._get_random_path("json")

        result = exporter.export_to_json(out_path)

        self.assertEqual(result, out_path)
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data, {key: val})

    def test_export_to_json_adapter_without_valid_digest(self):
        mock_vis = MagicMock()
        mock_vis.digest = "not_a_dict"

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = self._get_random_path("json")

        exporter.export_to_json(out_path)

        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data, {})

    def test_export_to_json_error_handling(self):
        exporter = DigestExporter(anomaly_visualizer=None)
        invalid_path = os.path.join(self.tmp_dir.name, "non_existent_folder", "out.json")

        with self.assertRaises(DigestExporterError):
            exporter.export_to_json(invalid_path)

    def test_export_to_html_adapter_with_valid_digest(self):
        mock_vis = MagicMock()
        key = f"k_{self._get_random_str()}"
        val = self._get_random_str()
        mock_vis.digest = {key: val}

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = self._get_random_path("html")

        result = exporter.export_to_html(out_path)

        self.assertEqual(result, out_path)
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(key, content)
        self.assertIn(val, content)

    def test_export_to_html_adapter_fallback(self):
        exporter = DigestExporter(anomaly_visualizer=None)
        out_path = self._get_random_path("html")

        exporter.export_to_html(out_path)

        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("{}", content)

    def test_export_to_html_error_handling(self):
        exporter = DigestExporter(anomaly_visualizer=None)
        invalid_path = os.path.join(self.tmp_dir.name, "non_existent_dir", "out.html")

        with self.assertRaises(DigestExporterError):
            exporter.export_to_html(invalid_path)

    def test_existing_digest_exporter_error_re_raised_directly(self):
        mock_vis = MagicMock()
        original_error = DigestExporterError(f"Custom_{self._get_random_str()}")
        mock_vis.get_summary_metrics.side_effect = original_error

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = self._get_random_path("json")

        with self.assertRaises(DigestExporterError) as ctx:
            exporter.export_json_report(out_path)

        self.assertIs(ctx.exception, original_error)


if __name__ == "__main__":
    unittest.main()