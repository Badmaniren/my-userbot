import json
import os
import random
import tempfile
import unittest
import uuid

from skills.digest_exporter import DigestExporter, DigestExporterError


class RealVisualizer:
    def __init__(self, metrics=None, text_report="", ascii_graph="", digest=None):
        self.metrics = metrics if metrics is not None else {}
        self.text_report = text_report
        self.ascii_graph = ascii_graph
        self.digest = digest if digest is not None else {}

    def get_summary_metrics(self):
        return self.metrics

    def render_text(self):
        return self.text_report

    def render_ascii_correlation_graph(self):
        return self.ascii_graph


class RealStabilityDigest:
    def __init__(self, streams=None):
        self.streams = streams if streams is not None else {}

    def export_digest_stream(self, stream_id):
        if stream_id in self.streams:
            return self.streams[stream_id]
        raise ValueError(f"Stream ID {stream_id} not found")


class TestDigestExporterIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_validate_structure(self):
        exporter = DigestExporter()

        valid_data = {
            f"key_{uuid.uuid4()}": random.randint(1, 1000),
            "status": "ok"
        }
        self.assertTrue(exporter.validate_structure(valid_data))

        self.assertFalse(exporter.validate_structure([1, 2, 3]))
        self.assertFalse(exporter.validate_structure(f"string_{uuid.uuid4()}"))
        self.assertFalse(exporter.validate_structure(12345))
        self.assertFalse(exporter.validate_structure(None))

    def test_export_json_report_creates_file_with_dynamic_data(self):
        random_key = f"metric_{uuid.uuid4()}"
        random_val = random.randint(100, 999)
        random_text = f"Text Report {uuid.uuid4()}"
        random_ascii = f"ASCII Graph {uuid.uuid4()}"

        visualizer = RealVisualizer(
            metrics={random_key: random_val},
            text_report=random_text,
            ascii_graph=random_ascii
        )
        exporter = DigestExporter(anomaly_visualizer=visualizer)

        output_path = os.path.join(self.temp_dir.name, f"report_{uuid.uuid4()}.json")
        returned_path = exporter.export_json_report(output_path)

        self.assertEqual(returned_path, output_path)
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get(random_key), random_val)
        self.assertEqual(data.get("text_report"), random_text)
        self.assertEqual(data.get("ascii_graph"), random_ascii)

    def test_export_html_report_creates_file_with_dynamic_data(self):
        random_text = f"HTML Text {uuid.uuid4()}"
        random_ascii = f"HTML ASCII {uuid.uuid4()}"
        random_metric_val = str(uuid.uuid4())

        visualizer = RealVisualizer(
            metrics={"uuid": random_metric_val},
            text_report=random_text,
            ascii_graph=random_ascii
        )
        exporter = DigestExporter(anomaly_visualizer=visualizer)

        output_path = os.path.join(self.temp_dir.name, f"report_{uuid.uuid4()}.html")
        returned_path = exporter.export_html_report(output_path)

        self.assertEqual(returned_path, output_path)
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<h1>Stability Digest Report</h1>", content)
        self.assertIn(random_metric_val, content)
        self.assertIn(random_text, content)
        self.assertIn(random_ascii, content)

    def test_export_markdown_report_creates_file_with_dynamic_data(self):
        random_text = f"MD Text {uuid.uuid4()}"
        random_ascii = f"MD ASCII {uuid.uuid4()}"
        random_val = random.randint(1000, 9999)

        visualizer = RealVisualizer(
            metrics={"val": random_val},
            text_report=random_text,
            ascii_graph=random_ascii
        )
        exporter = DigestExporter(anomaly_visualizer=visualizer)

        output_path = os.path.join(self.temp_dir.name, f"report_{uuid.uuid4()}.md")
        returned_path = exporter.export_markdown_report(output_path)

        self.assertEqual(returned_path, output_path)
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("# Stability Digest Report", content)
        self.assertIn("## Metrics", content)
        self.assertIn(str(random_val), content)
        self.assertIn(random_text, content)
        self.assertIn(random_ascii, content)

    def test_export_stream_to_json_creates_file_with_stream_payload(self):
        stream_id = f"stream_{uuid.uuid4()}"
        payload = {
            "stream_id": stream_id,
            "events": [random.randint(1, 100) for _ in range(3)],
            "tag": str(uuid.uuid4())
        }
        digest = RealStabilityDigest(streams={stream_id: payload})
        exporter = DigestExporter(stability_digest=digest)

        output_path = os.path.join(self.temp_dir.name, f"stream_{uuid.uuid4()}.json")
        returned_path = exporter.export_stream_to_json(stream_id, output_path)

        self.assertEqual(returned_path, output_path)
        self.assertTrue(os.path.exists(output_path))

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data, payload)

    def test_export_to_json_html_markdown_adapters(self):
        digest_dict = {
            "id": str(uuid.uuid4()),
            "count": random.randint(10, 50)
        }
        visualizer = RealVisualizer(digest=digest_dict)
        exporter = DigestExporter(anomaly_visualizer=visualizer)

        json_path = os.path.join(self.temp_dir.name, f"adapter_{uuid.uuid4()}.json")
        exporter.export_to_json(json_path)
        self.assertTrue(os.path.exists(json_path))
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data, digest_dict)

        html_path = os.path.join(self.temp_dir.name, f"adapter_{uuid.uuid4()}.html")
        exporter.export_to_html(html_path)
        self.assertTrue(os.path.exists(html_path))
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        self.assertIn(digest_dict["id"], html_content)

        md_path = os.path.join(self.temp_dir.name, f"adapter_{uuid.uuid4()}.md")
        exporter.export_to_markdown(md_path)
        self.assertTrue(os.path.exists(md_path))
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        self.assertIn(digest_dict["id"], md_content)