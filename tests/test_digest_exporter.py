import io
import json
import os
import random
import string
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporterInquisition(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix=f"inq_{random.randint(1000, 9999)}_")

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for file in files:
                try:
                    os.remove(os.path.join(root, file))
                except OSError:
                    pass
            for dir_name in dirs:
                try:
                    os.rmdir(os.path.join(root, dir_name))
                except OSError:
                    pass
        try:
            os.rmdir(self.test_dir)
        except OSError:
            pass

    def _generate_random_string(self, length=12):
        chars = string.ascii_letters + string.digits
        return "".join(random.choices(chars, k=length))

    def _generate_random_payload(self):
        return {
            self._generate_random_string(8): self._generate_random_string(16),
            self._generate_random_string(6): random.randint(100, 99999),
            self._generate_random_string(5): [random.random() for _ in range(4)],
        }

    def test_export_json_report_success_and_contents(self):
        fake_metrics = self._generate_random_payload()
        fake_text = self._generate_random_string(32)
        fake_ascii = self._generate_random_string(40)

        mock_visualizer = MagicMock()
        mock_visualizer.get_summary_metrics.return_value = fake_metrics
        mock_visualizer.render_text.return_value = fake_text
        mock_visualizer.render_ascii_correlation_graph.return_value = fake_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        filename = f"{self._generate_random_string(10)}.json"
        target_path = os.path.join(self.test_dir, filename)

        res = exporter.export_json_report(target_path)
        self.assertEqual(res, target_path)
        self.assertTrue(os.path.isfile(target_path))

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("text_report"), fake_text)
        self.assertEqual(data.get("ascii_graph"), fake_ascii)
        for k, v in fake_metrics.items():
            self.assertEqual(data.get(k), v)

    def test_export_json_report_without_visualizer(self):
        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=None)
        filename = f"{self._generate_random_string(10)}.json"
        target_path = os.path.join(self.test_dir, filename)

        res = exporter.export_json_report(target_path)
        self.assertEqual(res, target_path)

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data.get("text_report"), "")
        self.assertEqual(data.get("ascii_graph"), "")
        self.assertEqual(len(data.keys()), 2)

    def test_export_json_report_handles_io_exception(self):
        mock_visualizer = MagicMock()
        mock_visualizer.get_summary_metrics.return_value = {}
        mock_visualizer.render_text.return_value = ""
        mock_visualizer.render_ascii_correlation_graph.return_value = ""

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        invalid_path = os.path.join(self.test_dir, "non_existent_folder_abc", f"{self._generate_random_string()}.json")

        with self.assertRaises(DigestExporterError):
            exporter.export_json_report(invalid_path)

    def test_export_html_report_success_and_contents(self):
        fake_metrics = self._generate_random_payload()
        fake_text = self._generate_random_string(24)
        fake_ascii = self._generate_random_string(28)

        mock_visualizer = MagicMock()
        mock_visualizer.get_summary_metrics.return_value = fake_metrics
        mock_visualizer.render_text.return_value = fake_text
        mock_visualizer.render_ascii_correlation_graph.return_value = fake_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        filename = f"{self._generate_random_string(8)}.html"
        target_path = os.path.join(self.test_dir, filename)

        res = exporter.export_html_report(target_path)
        self.assertEqual(res, target_path)

        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("<html>", content)
        self.assertIn(fake_text, content)
        self.assertIn(fake_ascii, content)
        self.assertIn(str(fake_metrics), content)

    def test_export_html_report_exception_propagation(self):
        exporter = DigestExporter(anomaly_visualizer=None)
        invalid_path = os.path.join(self.test_dir, "ghost_dir", f"{self._generate_random_string()}.html")

        with self.assertRaises(DigestExporterError):
            exporter.export_html_report(invalid_path)

    def test_export_stream_to_json_success(self):
        stream_id = self._generate_random_string(14)
        expected_data = {
            self._generate_random_string(5): self._generate_random_string(12),
            "random_int": random.randint(1, 10000),
        }

        mock_digest = MagicMock()
        mock_digest.export_digest_stream.return_value = expected_data

        exporter = DigestExporter(stability_digest=mock_digest)
        filename = f"{self._generate_random_string(10)}.json"
        target_path = os.path.join(self.test_dir, filename)

        res = exporter.export_stream_to_json(stream_id, target_path)
        self.assertEqual(res, target_path)
        mock_digest.export_digest_stream.assert_called_once_with(stream_id)

        with open(target_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        self.assertEqual(loaded_data, expected_data)

    def test_export_stream_to_json_digest_failure(self):
        stream_id = self._generate_random_string(10)
        mock_digest = MagicMock()
        error_msg = self._generate_random_string(20)
        mock_digest.export_digest_stream.side_effect = RuntimeError(error_msg)

        exporter = DigestExporter(stability_digest=mock_digest)
        filename = f"{self._generate_random_string(10)}.json"
        target_path = os.path.join(self.test_dir, filename)

        with self.assertRaises(DigestExporterError) as ctx:
            exporter.export_stream_to_json(stream_id, target_path)
        self.assertIn(error_msg, str(ctx.exception))

    def test_export_to_json_adapter(self):
        random_digest_dict = self._generate_random_payload()
        mock_visualizer = MagicMock()
        mock_visualizer.digest = random_digest_dict

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        filename = f"{self._generate_random_string(8)}.json"
        target_path = os.path.join(self.test_dir, filename)

        res = exporter.export_to_json(target_path)
        self.assertEqual(res, target_path)

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data, random_digest_dict)

    def test_export_to_json_adapter_empty_when_no_digest_attribute(self):
        mock_visualizer = MagicMock(spec=[])
        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        filename = f"{self._generate_random_string(8)}.json"
        target_path = os.path.join(self.test_dir, filename)

        res = exporter.export_to_json(target_path)
        self.assertEqual(res, target_path)

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data, {})

    def test_export_to_html_adapter(self):
        random_digest_dict = self._generate_random_payload()
        mock_visualizer = MagicMock()
        mock_visualizer.digest = random_digest_dict

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        filename = f"{self._generate_random_string(8)}.html"
        target_path = os.path.join(self.test_dir, filename)

        res = exporter.export_to_html(target_path)
        self.assertEqual(res, target_path)

        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()

        serialized_fragment = json.dumps(random_digest_dict)
        self.assertIn(f"<pre>{serialized_fragment}</pre>", content)

    def test_export_to_html_adapter_io_error(self):
        mock_visualizer = MagicMock()
        mock_visualizer.digest = self._generate_random_payload()
        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        bad_path = os.path.join(self.test_dir, "missing_subdir", f"{self._generate_random_string()}.html")

        with self.assertRaises(DigestExporterError):
            exporter.export_to_html(bad_path)

    def test_export_markdown_report_success_and_contents(self):
        fake_metrics = self._generate_random_payload()
        fake_text = self._generate_random_string(24)
        fake_ascii = self._generate_random_string(28)

        mock_visualizer = MagicMock()
        mock_visualizer.get_summary_metrics.return_value = fake_metrics
        mock_visualizer.render_text.return_value = fake_text
        mock_visualizer.render_ascii_correlation_graph.return_value = fake_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        filename = f"{self._generate_random_string(8)}.md"
        target_path = os.path.join(self.test_dir, filename)

        res = exporter.export_markdown_report(target_path)
        self.assertEqual(res, target_path)

        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("# Stability Digest Report", content)
        self.assertIn(fake_text, content)
        self.assertIn(fake_ascii, content)

    def test_export_to_markdown_adapter(self):
        random_digest_dict = self._generate_random_payload()
        mock_visualizer = MagicMock()
        mock_visualizer.digest = random_digest_dict

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        filename = f"{self._generate_random_string(8)}.md"
        target_path = os.path.join(self.test_dir, filename)

        res = exporter.export_to_markdown(target_path)
        self.assertEqual(res, target_path)

        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("# Digest Data", content)

    def test_rethrow_existing_digest_exporter_error(self):
        mock_digest = MagicMock()
        sentinel_message = self._generate_random_string(30)
        mock_digest.export_digest_stream.side_effect = DigestExporterError(sentinel_message)

        exporter = DigestExporter(stability_digest=mock_digest)
        filename = f"{self._generate_random_string(8)}.json"
        target_path = os.path.join(self.test_dir, filename)

        with self.assertRaises(DigestExporterError) as ctx:
            exporter.export_stream_to_json("random_stream", target_path)
        self.assertEqual(str(ctx.exception), sentinel_message)


if __name__ == "__main__":
    unittest.main()