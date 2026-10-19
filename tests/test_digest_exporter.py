import io
import json
import os
import random
import string
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from skills.digest_exporter import DigestExporter, DigestExporterError


def _rand_str(length=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def _rand_dict():
    return {
        _rand_str(8): _rand_str(16),
        _rand_str(6): random.randint(1, 10000),
        _rand_str(5): random.choice([True, False])
    }


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def test_export_json_report_success_with_dict_metrics(self):
        mock_vis = MagicMock()
        mock_digest = MagicMock()

        key1 = _rand_str(8)
        val1 = _rand_str(15)
        metrics = {key1: val1, _rand_str(5): random.randint(10, 500)}
        text_rep = _rand_str(30)
        ascii_rep = _rand_str(40)

        mock_vis.get_summary_metrics.return_value = metrics
        mock_vis.render_text.return_value = text_rep
        mock_vis.render_ascii_correlation_graph.return_value = ascii_rep

        exporter = DigestExporter(stability_digest=mock_digest, anomaly_visualizer=mock_vis)

        filename = f"{_rand_str(10)}.json"
        out_path = os.path.join(self.tmp_dir.name, filename)

        res = exporter.export_json_report(out_path)
        self.assertEqual(res, out_path)
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        self.assertEqual(loaded.get(key1), val1)
        self.assertEqual(loaded.get("text_report"), text_rep)
        self.assertEqual(loaded.get("ascii_graph"), ascii_rep)

    def test_export_json_report_metrics_non_dict(self):
        mock_vis = MagicMock()
        text_rep = _rand_str(20)
        ascii_rep = _rand_str(25)

        mock_vis.get_summary_metrics.return_value = _rand_str(10)
        mock_vis.render_text.return_value = text_rep
        mock_vis.render_ascii_correlation_graph.return_value = ascii_rep

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = os.path.join(self.tmp_dir.name, f"{_rand_str(8)}.json")

        res = exporter.export_json_report(out_path)
        self.assertEqual(res, out_path)

        with open(out_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        self.assertIn("text_report", loaded)
        self.assertEqual(loaded["text_report"], text_rep)
        self.assertEqual(loaded["ascii_graph"], ascii_rep)

    def test_export_json_report_raises_digest_exporter_error(self):
        mock_vis = MagicMock()
        err_msg = _rand_str(20)
        mock_vis.get_summary_metrics.side_effect = RuntimeError(err_msg)

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = os.path.join(self.tmp_dir.name, f"{_rand_str(8)}.json")

        with self.assertRaises(DigestExporterError) as ctx:
            exporter.export_json_report(out_path)
        self.assertIn(err_msg, str(ctx.exception))

    def test_export_json_report_propagates_existing_digest_exporter_error(self):
        mock_vis = MagicMock()
        err_msg = _rand_str(15)
        mock_vis.get_summary_metrics.side_effect = DigestExporterError(err_msg)

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = os.path.join(self.tmp_dir.name, f"{_rand_str(8)}.json")

        with self.assertRaises(DigestExporterError) as ctx:
            exporter.export_json_report(out_path)
        self.assertIn(err_msg, str(ctx.exception))

    def test_export_html_report_success(self):
        mock_vis = MagicMock()
        metrics = {_rand_str(6): _rand_str(10)}
        text_rep = _rand_str(18)
        ascii_rep = _rand_str(22)

        mock_vis.get_summary_metrics.return_value = metrics
        mock_vis.render_text.return_value = text_rep
        mock_vis.render_ascii_correlation_graph.return_value = ascii_rep

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = os.path.join(self.tmp_dir.name, f"{_rand_str(8)}.html")

        res = exporter.export_html_report(out_path)
        self.assertEqual(res, out_path)
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn(text_rep, content)
        self.assertIn(ascii_rep, content)
        self.assertIn(str(metrics), content)

    def test_export_html_report_error(self):
        mock_vis = MagicMock()
        mock_vis.get_summary_metrics.return_value = {}
        mock_vis.render_text.side_effect = IOError(_rand_str(12))

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = os.path.join(self.tmp_dir.name, f"{_rand_str(8)}.html")

        with self.assertRaises(DigestExporterError):
            exporter.export_html_report(out_path)

    def test_export_stream_to_json_success(self):
        mock_digest = MagicMock()
        stream_id = _rand_str(10)
        expected_stream_data = _rand_dict()

        mock_digest.export_digest_stream.return_value = expected_stream_data

        exporter = DigestExporter(stability_digest=mock_digest)
        out_path = os.path.join(self.tmp_dir.name, f"{_rand_str(8)}.json")

        res = exporter.export_stream_to_json(stream_id, out_path)
        mock_digest.export_digest_stream.assert_called_once_with(stream_id)
        self.assertEqual(res, out_path)

        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data, expected_stream_data)

    def test_export_stream_to_json_error(self):
        mock_digest = MagicMock()
        stream_id = _rand_str(10)
        mock_digest.export_digest_stream.side_effect = ValueError(_rand_str(14))

        exporter = DigestExporter(stability_digest=mock_digest)
        out_path = os.path.join(self.tmp_dir.name, f"{_rand_str(8)}.json")

        with self.assertRaises(DigestExporterError):
            exporter.export_stream_to_json(stream_id, out_path)

    def test_export_to_json_with_visualizer_digest_dict(self):
        mock_vis = MagicMock()
        payload = _rand_dict()
        mock_vis.digest = payload

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = os.path.join(self.tmp_dir.name, f"{_rand_str(8)}.json")

        res = exporter.export_to_json(out_path)
        self.assertEqual(res, out_path)

        with open(out_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        self.assertEqual(loaded, payload)

    def test_export_to_json_without_visualizer_digest(self):
        exporter = DigestExporter(anomaly_visualizer=None)
        out_path = os.path.join(self.tmp_dir.name, f"{_rand_str(8)}.json")

        res = exporter.export_to_json(out_path)
        self.assertEqual(res, out_path)

        with open(out_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        self.assertEqual(loaded, {})

    def test_export_to_json_file_error(self):
        exporter = DigestExporter(anomaly_visualizer=None)
        invalid_path = os.path.join(self.tmp_dir.name, _rand_str(8), _rand_str(8), "file.json")

        with self.assertRaises(DigestExporterError):
            exporter.export_to_json(invalid_path)

    def test_export_to_html_with_visualizer_digest(self):
        mock_vis = MagicMock()
        payload = _rand_dict()
        mock_vis.digest = payload

        exporter = DigestExporter(anomaly_visualizer=mock_vis)
        out_path = os.path.join(self.tmp_dir.name, f"{_rand_str(8)}.html")

        res = exporter.export_to_html(out_path)
        self.assertEqual(res, out_path)

        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()

        serialized = json.dumps(payload)
        self.assertIn(serialized, content)
        self.assertTrue(content.startswith("<html><body><pre>"))

    def test_export_to_html_without_visualizer(self):
        exporter = DigestExporter(anomaly_visualizer=None)
        out_path = os.path.join(self.tmp_dir.name, f"{_rand_str(8)}.html")

        res = exporter.export_to_html(out_path)
        self.assertEqual(res, out_path)

        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("{}", content)

    def test_export_to_html_file_error(self):
        exporter = DigestExporter(anomaly_visualizer=None)
        invalid_path = os.path.join(self.tmp_dir.name, _rand_str(6), _rand_str(6), "err.html")

        with self.assertRaises(DigestExporterError):
            exporter.export_to_html(invalid_path)


if __name__ == "__main__":
    unittest.main()