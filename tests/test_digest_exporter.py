import json
import unittest
import uuid
import random
import string
import io
from unittest.mock import patch, MagicMock, mock_open

from skills.digest_exporter import DigestExporter, DigestExporterError


# --- Unit Tests ---

class TestDigestExporter(unittest.TestCase):

    def _generate_random_string(self, length=12):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def _generate_random_path(self, ext="json"):
        return f"/tmp/{uuid.uuid4().hex}.{ext}"

    def _generate_random_dict(self):
        return {self._generate_random_string(): self._generate_random_string() for _ in range(3)}

    def test_export_json_report_success(self):
        random_path = self._generate_random_path()
        random_metrics = self._generate_random_dict()
        random_text = self._generate_random_string(50)
        random_ascii = self._generate_random_string(100)

        mock_vis = MagicMock()
        mock_vis.get_summary_metrics.return_value = random_metrics
        mock_vis.render_text.return_value = random_text
        mock_vis.render_ascii_correlation_graph.return_value = random_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_vis)

        with patch("builtins.open", mock_open()) as m_open:
            with patch("json.dump") as m_json_dump:
                result = exporter.export_json_report(random_path)

                self.assertEqual(result, random_path)
                m_json_dump.assert_called_once()
                args, _ = m_json_dump.call_args
                exported_data = args[0]

                self.assertEqual(exported_data['text_report'], random_text)
                self.assertEqual(exported_data['ascii_graph'], random_ascii)
                for k, v in random_metrics.items():
                    self.assertEqual(exported_data[k], v)

    def test_export_html_report_success(self):
        random_path = self._generate_random_path("html")
        random_metrics = self._generate_random_dict()
        random_text = f"TEXT_{uuid.uuid4().hex}"
        random_ascii = f"ASCII_{uuid.uuid4().hex}"

        mock_vis = MagicMock()
        mock_vis.get_summary_metrics.return_value = random_metrics
        mock_vis.render_text.return_value = random_text
        mock_vis.render_ascii_correlation_graph.return_value = random_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_vis)

        with patch("builtins.open", mock_open()) as m_open:
            result = exporter.export_html_report(random_path)

            self.assertEqual(result, random_path)
            handle = m_open()
            written_content = "".join(call.args[0] for call in handle.write.call_args_list)

            self.assertIn(random_text, written_content)
            self.assertIn(random_ascii, written_content)
            self.assertIn(str(random_metrics), written_content)

    def test_export_markdown_report_success(self):
        random_path = self._generate_random_path("md")
        random_metrics = self._generate_random_dict()
        random_text = f"TEXT_{uuid.uuid4().hex}"
        random_ascii = f"ASCII_{uuid.uuid4().hex}"

        mock_vis = MagicMock()
        mock_vis.get_summary_metrics.return_value = random_metrics
        mock_vis.render_text.return_value = random_text
        mock_vis.render_ascii_correlation_graph.return_value = random_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_vis)

        with patch("builtins.open", mock_open()) as m_open:
            result = exporter.export_markdown_report(random_path)

            self.assertEqual(result, random_path)
            handle = m_open()
            written_content = "".join(call.args[0] for call in handle.write.call_args_list)

            self.assertIn("# Stability Digest Report", written_content)
            self.assertIn(random_text, written_content)
            self.assertIn(random_ascii, written_content)

    def test_export_stream_to_json_success(self):
        random_path = self._generate_random_path()
        random_stream_id = uuid.uuid4().hex
        random_data = self._generate_random_dict()

        mock_digest = MagicMock()
        mock_digest.export_digest_stream.return_value = random_data

        exporter = DigestExporter(stability_digest=mock_digest)

        with patch("builtins.open", mock_open()):
            with patch("json.dump") as m_json_dump:
                result = exporter.export_stream_to_json(random_stream_id, random_path)

                self.assertEqual(result, random_path)
                mock_digest.export_digest_stream.assert_called_once_with(random_stream_id)
                m_json_dump.assert_called_once_with(random_data, unittest.mock.ANY, ensure_ascii=False, indent=4)

    def test_export_to_json_adapter_logic(self):
        random_path = self._generate_random_path()
        random_digest_data = self._generate_random_dict()

        mock_vis = MagicMock()
        mock_vis.digest = random_digest_data

        exporter = DigestExporter(anomaly_visualizer=mock_vis)

        with patch("builtins.open", mock_open()):
            with patch("json.dump") as m_json_dump:
                exporter.export_to_json(random_path)
                m_json_dump.assert_called_once()
                self.assertEqual(m_json_dump.call_args[0][0], random_digest_data)

    def test_export_to_html_adapter_logic(self):
        random_path = self._generate_random_path("html")
        random_digest_data = self._generate_random_dict()

        mock_vis = MagicMock()
        mock_vis.digest = random_digest_data

        exporter = DigestExporter(anomaly_visualizer=mock_vis)

        with patch("builtins.open", mock_open()) as m_open:
            with patch("json.dumps") as m_json_dumps:
                m_json_dumps.return_value = "MOCK_JSON_STRING"
                exporter.export_to_html(random_path)

                m_json_dumps.assert_called_once_with(random_digest_data, ensure_ascii=False)
                handle = m_open()
                written_content = "".join(call.args[0] for call in handle.write.call_args_list)
                self.assertIn("MOCK_JSON_STRING", written_content)

    def test_export_to_markdown_adapter_logic(self):
        random_path = self._generate_random_path("md")
        random_digest_data = self._generate_random_dict()

        mock_vis = MagicMock()
        mock_vis.digest = random_digest_data

        exporter = DigestExporter(anomaly_visualizer=mock_vis)

        with patch("builtins.open", mock_open()) as m_open:
            exporter.export_to_markdown(random_path)
            handle = m_open()
            written_content = "".join(call.args[0] for call in handle.write.call_args_list)
            self.assertIn("# Digest Data", written_content)

    def test_error_wrapping_on_failure(self):
        mock_vis = MagicMock()
        mock_vis.get_summary_metrics.side_effect = Exception("CRITICAL_SYSTEM_FAILURE")

        exporter = DigestExporter(anomaly_visualizer=mock_vis)

        with self.assertRaises(DigestExporterError) as cm:
            exporter.export_json_report(self._generate_random_path())

        self.assertIn("CRITICAL_SYSTEM_FAILURE", str(cm.exception))

    def test_file_write_error_handling(self):
        mock_vis = MagicMock()
        mock_vis.get_summary_metrics.return_value = {}
        exporter = DigestExporter(anomaly_visualizer=mock_vis)

        with patch("builtins.open", side_effect=IOError("PERMISSION_DENIED")):
            with self.assertRaises(DigestExporterError) as cm:
                exporter.export_json_report(self._generate_random_path())
            self.assertIn("PERMISSION_DENIED", str(cm.exception))

    def test_export_to_json_empty_visualizer(self):
        exporter = DigestExporter(anomaly_visualizer=None)
        random_path = self._generate_random_path()

        with patch("builtins.open", mock_open()):
            with patch("json.dump") as m_json_dump:
                exporter.export_to_json(random_path)
                m_json_dump.assert_called_once_with({}, unittest.mock.ANY, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    unittest.main()
