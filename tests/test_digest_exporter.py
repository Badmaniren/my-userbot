import unittest
from unittest.mock import MagicMock, patch
import json
import uuid
import random
import os
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.output_path = f"{uuid.uuid4().hex}.json"
        self.html_output_path = f"{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex
        
        self.mock_digest = MagicMock()
        self.mock_visualizer = MagicMock()
        
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
        ascii_graph_content = uuid.uuid4().hex

        self.mock_visualizer.get_summary_metrics.return_value = {metric_key: metric_val}
        self.mock_visualizer.render_text.return_value = text_content
        self.mock_visualizer.render_ascii_correlation_graph.return_value = ascii_graph_content

        result_path = self.exporter.export_json_report(self.output_path)

        self.assertEqual(result_path, self.output_path)
        self.assertTrue(os.path.exists(self.output_path))

        with open(self.output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get(metric_key), metric_val)
        self.assertEqual(data.get("text_report"), text_content)
        self.assertEqual(data.get("ascii_graph"), ascii_graph_content)

    def test_export_json_report_non_dict_metrics(self):
        self.mock_visualizer.get_summary_metrics.return_value = [random.randint(1, 100)]
        text_content = uuid.uuid4().hex
        ascii_graph_content = uuid.uuid4().hex

        self.mock_visualizer.render_text.return_value = text_content
        self.mock_visualizer.render_ascii_correlation_graph.return_value = ascii_graph_content

        self.exporter.export_json_report(self.output_path)

        with open(self.output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIn("text_report", data)
        self.assertIn("ascii_graph", data)
        self.assertEqual(data["text_report"], text_content)

    def test_export_json_report_raises_exporter_error(self):
        self.mock_visualizer.get_summary_metrics.side_effect = RuntimeError(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(self.output_path)

    def test_export_html_report_success(self):
        metrics_val = uuid.uuid4().hex
        text_rep = uuid.uuid4().hex
        ascii_rep = uuid.uuid4().hex

        self.mock_visualizer.get_summary_metrics.return_value = metrics_val
        self.mock_visualizer.render_text.return_value = text_rep
        self.mock_visualizer.render_ascii_correlation_graph.return_value = ascii_rep

        result_path = self.exporter.export_html_report(self.html_output_path)

        self.assertEqual(result_path, self.html_output_path)
        self.assertTrue(os.path.exists(self.html_output_path))

        with open(self.html_output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(str(metrics_val), content)
        self.assertIn(text_rep, content)
        self.assertIn(ascii_rep, content)
        self.assertIn("<html>", content)

    def test_export_html_report_raises_exporter_error(self):
        self.mock_visualizer.render_text.side_effect = ValueError(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_html_report(self.html_output_path)

    def test_export_stream_to_json_success(self):
        stream_payload = {uuid.uuid4().hex: random.randint(1, 500)}
        self.mock_digest.export_digest_stream.return_value = stream_payload

        result_path = self.exporter.export_stream_to_json(self.stream_id, self.output_path)

        self.assertEqual(result_path, self.output_path)
        self.mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)

        with open(self.output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data, stream_payload)

    def test_export_stream_to_json_raises_exporter_error(self):
        self.mock_digest.export_digest_stream.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_stream_to_json(self.stream_id, self.output_path)

    def test_export_to_json_adapter_with_visualizer_dict(self):
        digest_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_visualizer.digest = digest_dict

        result_path = self.exporter.export_to_json(self.output_path)

        self.assertEqual(result_path, self.output_path)
        with open(self.output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data, digest_dict)

    def test_export_to_json_adapter_with_digest_dict(self):
        exporter_no_vis = DigestExporter(stability_digest=self.mock_digest, anomaly_visualizer=None)
        digest_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_digest.digest = digest_dict

        result_path = exporter_no_vis.export_to_json(self.output_path)

        self.assertEqual(result_path, self.output_path)
        with open(self.output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data, digest_dict)

    def test_export_to_json_adapter_with_summary_metrics(self):
        exporter_summary = DigestExporter(stability_digest=self.mock_digest, anomaly_visualizer=None)
        metrics_dict = {uuid.uuid4().hex: random.random()}
        self.mock_digest.get_summary_metrics.return_value = metrics_dict

        result_path = exporter_summary.export_to_json(self.output_path)

        self.assertEqual(result_path, self.output_path)
        with open(self.output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data, metrics_dict)

    def test_export_to_json_adapter_raises_exporter_error(self):
        exporter_faulty = DigestExporter(stability_digest=None, anomaly_visualizer=None)
        with patch("builtins.open", side_effect=IOError(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                exporter_faulty.export_to_json(self.output_path)

    def test_export_to_html_adapter_success(self):
        digest_dict = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_visualizer.digest = digest_dict

        result_path = self.exporter.export_to_html(self.html_output_path)

        self.assertEqual(result_path, self.html_output_path)
        with open(self.html_output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Stability Digest Report", content)
        self.assertIn(json.dumps(digest_dict), content)

    def test_export_to_html_adapter_raises_exporter_error(self):
        with patch("builtins.open", side_effect=PermissionError(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_html(self.html_output_path)


if __name__ == "__main__":
    unittest.main()