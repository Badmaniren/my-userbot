import os
import json
import uuid
import random
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _generate_random_string(self, length=12):
        return "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=length))

    def test_init_and_attributes(self):
        digest_mock = MagicMock()
        visualizer_mock = MagicMock()
        exporter = DigestExporter(stability_digest=digest_mock, anomaly_visualizer=visualizer_mock)

        self.assertIs(exporter.digest, digest_mock)
        self.assertIs(exporter.visualizer, visualizer_mock)

    def test_export_json_report_success(self):
        visualizer_mock = MagicMock()
        metric_key = "metric_" + self._generate_random_string()
        metric_val = random.randint(100, 9999)
        text_payload = "text_" + self._generate_random_string()
        ascii_payload = "ascii_" + self._generate_random_string()

        visualizer_mock.get_summary_metrics.return_value = {metric_key: metric_val}
        visualizer_mock.render_text.return_value = text_payload
        visualizer_mock.render_ascii_correlation_graph.return_value = ascii_payload

        exporter = DigestExporter(anomaly_visualizer=visualizer_mock)
        output_file = os.path.join(self.temp_dir.name, f"out_{uuid.uuid4().hex}.json")

        result = exporter.export_json_report(output_file)

        self.assertEqual(result, output_file)
        self.assertTrue(os.path.exists(output_file))

        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get(metric_key), metric_val)
        self.assertEqual(data.get("text_report"), text_payload)
        self.assertEqual(data.get("ascii_graph"), ascii_payload)

    def test_export_json_report_non_dict_metrics(self):
        visualizer_mock = MagicMock()
        text_payload = "text_" + self._generate_random_string()
        ascii_payload = "ascii_" + self._generate_random_string()

        visualizer_mock.get_summary_metrics.return_value = None
        visualizer_mock.render_text.return_value = text_payload
        visualizer_mock.render_ascii_correlation_graph.return_value = ascii_payload

        exporter = DigestExporter(anomaly_visualizer=visualizer_mock)
        output_file = os.path.join(self.temp_dir.name, f"out_{uuid.uuid4().hex}.json")

        result = exporter.export_json_report(output_file)
        self.assertEqual(result, output_file)

        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("text_report"), text_payload)
        self.assertEqual(data.get("ascii_graph"), ascii_payload)

    def test_export_json_report_failure_raises_digest_exporter_error(self):
        visualizer_mock = MagicMock()
        visualizer_mock.get_summary_metrics.side_effect = RuntimeError("Visualizer failure: " + uuid.uuid4().hex)

        exporter = DigestExporter(anomaly_visualizer=visualizer_mock)
        output_file = os.path.join(self.temp_dir.name, f"out_{uuid.uuid4().hex}.json")

        with self.assertRaises(DigestExporterError):
            exporter.export_json_report(output_file)

    def test_export_html_report_success(self):
        visualizer_mock = MagicMock()
        metric_key = "key_" + self._generate_random_string()
        metric_val = uuid.uuid4().hex
        text_payload = "report_text_" + self._generate_random_string()
        ascii_payload = "ascii_graph_" + self._generate_random_string()

        visualizer_mock.get_summary_metrics.return_value = {metric_key: metric_val}
        visualizer_mock.render_text.return_value = text_payload
        visualizer_mock.render_ascii_correlation_graph.return_value = ascii_payload

        exporter = DigestExporter(anomaly_visualizer=visualizer_mock)
        output_file = os.path.join(self.temp_dir.name, f"out_{uuid.uuid4().hex}.html")

        result = exporter.export_html_report(output_file)
        self.assertEqual(result, output_file)
        self.assertTrue(os.path.exists(output_file))

        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn(metric_key, content)
        self.assertIn(metric_val, content)
        self.assertIn(text_payload, content)
        self.assertIn(ascii_payload, content)

    def test_export_html_report_failure_raises_digest_exporter_error(self):
        visualizer_mock = MagicMock()
        visualizer_mock.render_text.side_effect = ValueError("Render error: " + uuid.uuid4().hex)

        exporter = DigestExporter(anomaly_visualizer=visualizer_mock)
        output_file = os.path.join(self.temp_dir.name, f"out_{uuid.uuid4().hex}.html")

        with self.assertRaises(DigestExporterError):
            exporter.export_html_report(output_file)

    def test_export_stream_to_json_success(self):
        digest_mock = MagicMock()
        stream_id = "stream_" + uuid.uuid4().hex
        payload_key = "stream_key_" + self._generate_random_string()
        payload_val = random.randint(1000, 99999)
        mock_data = {payload_key: payload_val, "session": uuid.uuid4().hex}

        digest_mock.export_digest_stream.return_value = mock_data

        exporter = DigestExporter(stability_digest=digest_mock)
        output_file = os.path.join(self.temp_dir.name, f"stream_{uuid.uuid4().hex}.json")

        result = exporter.export_stream_to_json(stream_id, output_file)
        self.assertEqual(result, output_file)
        digest_mock.export_digest_stream.assert_called_once_with(stream_id)

        with open(output_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data.get(payload_key), payload_val)
        self.assertEqual(saved_data.get("session"), mock_data["session"])

    def test_export_stream_to_json_failure_raises_digest_exporter_error(self):
        digest_mock = MagicMock()
        digest_mock.export_digest_stream.side_effect = KeyError("Stream not found: " + uuid.uuid4().hex)

        exporter = DigestExporter(stability_digest=digest_mock)
        output_file = os.path.join(self.temp_dir.name, f"stream_{uuid.uuid4().hex}.json")

        with self.assertRaises(DigestExporterError):
            exporter.export_stream_to_json("random_id_" + uuid.uuid4().hex, output_file)

    def test_export_to_json_with_digest_dict(self):
        visualizer_mock = MagicMock()
        random_key = "k_" + self._generate_random_string()
        random_val = "v_" + self._generate_random_string()
        visualizer_mock.digest = {random_key: random_val}

        exporter = DigestExporter(anomaly_visualizer=visualizer_mock)
        output_file = os.path.join(self.temp_dir.name, f"adapter_{uuid.uuid4().hex}.json")

        result = exporter.export_to_json(output_file)
        self.assertEqual(result, output_file)

        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get(random_key), random_val)

    def test_export_to_json_without_visualizer_digest(self):
        visualizer_mock = MagicMock()
        del visualizer_mock.digest

        exporter = DigestExporter(anomaly_visualizer=visualizer_mock)
        output_file = os.path.join(self.temp_dir.name, f"adapter_empty_{uuid.uuid4().hex}.json")

        result = exporter.export_to_json(output_file)
        self.assertEqual(result, output_file)

        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data, {})

    def test_export_to_json_io_error_raises_digest_exporter_error(self):
        exporter = DigestExporter()
        invalid_path = os.path.join(self.temp_dir.name, "non_existent_subdir_" + uuid.uuid4().hex, "report.json")

        with self.assertRaises(DigestExporterError):
            exporter.export_to_json(invalid_path)

    def test_export_to_html_with_digest_dict(self):
        visualizer_mock = MagicMock()
        random_key = "prop_" + self._generate_random_string()
        random_val = uuid.uuid4().hex
        visualizer_mock.digest = {random_key: random_val}

        exporter = DigestExporter(anomaly_visualizer=visualizer_mock)
        output_file = os.path.join(self.temp_dir.name, f"adapter_{uuid.uuid4().hex}.html")

        result = exporter.export_to_html(output_file)
        self.assertEqual(result, output_file)

        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<html><body><pre>", content)
        self.assertIn(random_key, content)
        self.assertIn(random_val, content)

    def test_export_to_html_empty_visualizer(self):
        exporter = DigestExporter(anomaly_visualizer=None)
        output_file = os.path.join(self.temp_dir.name, f"adapter_none_{uuid.uuid4().hex}.html")

        result = exporter.export_to_html(output_file)
        self.assertEqual(result, output_file)

        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertEqual(content, "<html><body><pre>{}</pre></body></html>")

    def test_export_to_html_io_error_raises_digest_exporter_error(self):
        exporter = DigestExporter()
        invalid_path = os.path.join(self.temp_dir.name, "absent_dir_" + uuid.uuid4().hex, "file.html")

        with self.assertRaises(DigestExporterError):
            exporter.export_to_html(invalid_path)

    def test_rethrow_existing_digest_exporter_error(self):
        digest_mock = MagicMock()
        custom_msg = "Explicit failure: " + uuid.uuid4().hex
        digest_mock.export_digest_stream.side_effect = DigestExporterError(custom_msg)

        exporter = DigestExporter(stability_digest=digest_mock)
        output_file = os.path.join(self.temp_dir.name, f"file_{uuid.uuid4().hex}.json")

        with self.assertRaises(DigestExporterError) as cm:
            exporter.export_stream_to_json("stream_" + uuid.uuid4().hex, output_file)

        self.assertIn(custom_msg, str(cm.exception))


if __name__ == "__main__":
    unittest.main()