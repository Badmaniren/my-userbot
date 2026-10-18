import json
import os
import random
import tempfile
import unittest
import uuid

from skills.digest_exporter import DigestExporter, DigestExporterError


class SimpleVisualizer:
    """Реализация визуализатора для проверки контракта экспорта."""

    def __init__(self, metrics=None, text="", ascii_graph="", digest=None):
        self._metrics = metrics if metrics is not None else {}
        self._text = text
        self._ascii_graph = ascii_graph
        self.digest = digest

    def get_summary_metrics(self):
        return self._metrics

    def render_text(self):
        return self._text

    def render_ascii_correlation_graph(self):
        return self._ascii_graph


class SimpleDigest:
    """Реализация дайджеста для проверки экспорта потоков."""

    def __init__(self, streams=None):
        self._streams = streams if streams is not None else {}

    def export_digest_stream(self, stream_id: str):
        if stream_id in self._streams:
            return self._streams[stream_id]
        raise ValueError(f"Stream {stream_id} not found")


class TestDigestExporterIntegration(unittest.TestCase):
    """Интеграционные тесты для DigestExporter без использования мок-библиотек."""

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.temp_path = self.test_dir.name

    def tearDown(self):
        self.test_dir.cleanup()

    def test_export_json_report_with_visualizer(self):
        rand_key = f"metric_{uuid.uuid4().hex[:8]}"
        rand_val = random.randint(100, 9999)
        rand_text = f"Audit summary for execution {uuid.uuid4()}"
        rand_graph = f"ASCII_GRAPH_NODE_{uuid.uuid4().hex}"

        metrics = {rand_key: rand_val, "status": "active"}
        visualizer = SimpleVisualizer(
            metrics=metrics,
            text=rand_text,
            ascii_graph=rand_graph
        )
        exporter = DigestExporter(anomaly_visualizer=visualizer)

        file_name = f"report_{uuid.uuid4().hex}.json"
        out_path = os.path.join(self.temp_path, file_name)

        result_path = exporter.export_json_report(out_path)
        self.assertEqual(result_path, out_path)
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get(rand_key), rand_val)
        self.assertEqual(data.get("text_report"), rand_text)
        self.assertEqual(data.get("ascii_graph"), rand_graph)

    def test_export_html_report_with_visualizer(self):
        rand_token = f"token_{uuid.uuid4().hex}"
        rand_metric_val = random.uniform(10.5, 99.5)
        metrics = {"score": rand_metric_val}
        text_rep = f"Text report containing {rand_token}"
        ascii_rep = f"Graph line: {rand_token}"

        visualizer = SimpleVisualizer(
            metrics=metrics,
            text=text_rep,
            ascii_graph=ascii_rep
        )
        exporter = DigestExporter(anomaly_visualizer=visualizer)

        file_name = f"report_{uuid.uuid4().hex}.html"
        out_path = os.path.join(self.temp_path, file_name)

        result_path = exporter.export_html_report(out_path)
        self.assertEqual(result_path, out_path)
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        self.assertIn("Stability Digest Report", html_content)
        self.assertIn(rand_token, html_content)
        self.assertIn(str(rand_metric_val), html_content)

    def test_export_stream_to_json(self):
        rand_stream_id = f"stream_{uuid.uuid4().hex}"
        rand_payload = {
            "record_id": str(uuid.uuid4()),
            "anomaly_level": random.randint(1, 5),
            "signature": uuid.uuid4().hex
        }

        digest = SimpleDigest(streams={rand_stream_id: rand_payload})
        exporter = DigestExporter(stability_digest=digest)

        file_name = f"stream_{uuid.uuid4().hex}.json"
        out_path = os.path.join(self.temp_path, file_name)

        result_path = exporter.export_stream_to_json(rand_stream_id, out_path)
        self.assertEqual(result_path, out_path)
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data, rand_payload)
        self.assertEqual(saved_data["signature"], rand_payload["signature"])

    def test_export_to_json_and_html_adapters(self):
        rand_field = f"field_{uuid.uuid4().hex}"
        rand_value = f"value_{uuid.uuid4()}"
        digest_dict = {rand_field: rand_value}

        visualizer = SimpleVisualizer(digest=digest_dict)
        exporter = DigestExporter(anomaly_visualizer=visualizer)

        json_file = os.path.join(self.temp_path, f"adapter_{uuid.uuid4().hex}.json")
        exporter.export_to_json(json_file)
        self.assertTrue(os.path.exists(json_file))
        with open(json_file, "r", encoding="utf-8") as f:
            loaded_json = json.load(f)
        self.assertEqual(loaded_json.get(rand_field), rand_value)

        html_file = os.path.join(self.temp_path, f"adapter_{uuid.uuid4().hex}.html")
        exporter.export_to_html(html_file)
        self.assertTrue(os.path.exists(html_file))
        with open(html_file, "r", encoding="utf-8") as f:
            loaded_html = f.read()
        self.assertIn(rand_value, loaded_html)

        md_file = os.path.join(self.temp_path, f"adapter_{uuid.uuid4().hex}.md")
        exporter.export_to_markdown(md_file)
        self.assertTrue(os.path.exists(md_file))
        with open(md_file, "r", encoding="utf-8") as f:
            loaded_md = f.read()
        self.assertIn(rand_value, loaded_md)

    def test_export_markdown_report_with_visualizer(self):
        rand_token = f"md_token_{uuid.uuid4().hex}"
        metrics = {"score": 42}
        text_rep = f"MD report text {rand_token}"
        ascii_rep = f"MD graph {rand_token}"

        visualizer = SimpleVisualizer(
            metrics=metrics,
            text=text_rep,
            ascii_graph=ascii_rep
        )
        exporter = DigestExporter(anomaly_visualizer=visualizer)

        file_name = f"report_{uuid.uuid4().hex}.md"
        out_path = os.path.join(self.temp_path, file_name)

        result_path = exporter.export_markdown_report(out_path)
        self.assertEqual(result_path, out_path)
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        self.assertIn("# Stability Digest Report", md_content)
        self.assertIn(rand_token, md_content)

    def test_export_json_report_default_none_components(self):
        exporter = DigestExporter()
        out_path = os.path.join(self.temp_path, f"default_{uuid.uuid4().hex}.json")

        result_path = exporter.export_json_report(out_path)
        self.assertEqual(result_path, out_path)
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("text_report"), "")
        self.assertEqual(data.get("ascii_graph"), "")

    def test_export_to_invalid_path_raises_digest_exporter_error(self):
        exporter = DigestExporter()
        invalid_dir = os.path.join(self.temp_path, f"missing_{uuid.uuid4().hex}", "deep")
        invalid_file = os.path.join(invalid_dir, "report.json")

        with self.assertRaises(DigestExporterError):
            exporter.export_json_report(invalid_file)

        with self.assertRaises(DigestExporterError):
            exporter.export_html_report(invalid_file)

        with self.assertRaises(DigestExporterError):
            exporter.export_to_json(invalid_file)

        with self.assertRaises(DigestExporterError):
            exporter.export_to_html(invalid_file)

    def test_export_stream_missing_digest_raises_digest_exporter_error(self):
        exporter = DigestExporter()
        out_path = os.path.join(self.temp_path, f"missing_stream_{uuid.uuid4().hex}.json")

        with self.assertRaises(DigestExporterError):
            exporter.export_stream_to_json(str(uuid.uuid4()), out_path)


if __name__ == "__main__":
    unittest.main()