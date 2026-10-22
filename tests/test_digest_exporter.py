import unittest
from unittest.mock import patch, mock_open
import json
import uuid
import random
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporterInquisition(unittest.TestCase):

    def setUp(self):
        self.output_path = f"{uuid.uuid4().hex}.json"
        self.html_output_path = f"{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex

        self.mock_visualizer = unittest.mock.MagicMock()
        self.mock_digest = unittest.mock.MagicMock()

        self.metric_key = uuid.uuid4().hex
        self.metric_val = random.randint(1, 1000)
        self.text_rep_val = uuid.uuid4().hex
        self.ascii_rep_val = uuid.uuid4().hex

        self.mock_visualizer.get_summary_metrics.return_value = {self.metric_key: self.metric_val}
        self.mock_visualizer.render_text.return_value = self.text_rep_val
        self.mock_visualizer.render_ascii_correlation_graph.return_value = self.ascii_rep_val

        self.exporter = DigestExporter(stability_digest=self.mock_digest, anomaly_visualizer=self.mock_visualizer)

    def test_export_json_report_success(self):
        m_open = mock_open()
        with patch("builtins.open", m_open):
            res_path = self.exporter.export_json_report(self.output_path)
            self.assertEqual(res_path, self.output_path)
            m_open.assert_called_once_with(self.output_path, "w", encoding="utf-8")

            handle = m_open()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed = json.loads(written_data)

            self.assertEqual(parsed.get(self.metric_key), self.metric_val)
            self.assertEqual(parsed.get("text_report"), self.text_rep_val)
            self.assertEqual(parsed.get("ascii_graph"), self.ascii_rep_val)

    def test_export_json_report_handles_non_dict_metrics(self):
        non_dict_val = random.randint(5000, 9999)
        self.mock_visualizer.get_summary_metrics.return_value = non_dict_val

        m_open = mock_open()
        with patch("builtins.open", m_open):
            self.exporter.export_json_report(self.output_path)
            handle = m_open()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed = json.loads(written_data)

            self.assertNotIn(str(non_dict_val), parsed)
            self.assertEqual(parsed.get("text_report"), self.text_rep_val)
            self.assertEqual(parsed.get("ascii_graph"), self.ascii_rep_val)

    def test_export_json_report_raises_exporter_error_on_exception(self):
        err_msg = uuid.uuid4().hex
        self.mock_visualizer.get_summary_metrics.side_effect = Exception(err_msg)

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_json_report(self.output_path)
        self.assertIn(err_msg, str(ctx.exception))

    def test_export_html_report_success(self):
        m_open = mock_open()
        with patch("builtins.open", m_open):
            res_path = self.exporter.export_html_report(self.html_output_path)
            self.assertEqual(res_path, self.html_output_path)
            m_open.assert_called_once_with(self.html_output_path, "w", encoding="utf-8")

            handle = m_open()
            html_content = "".join(call.args[0] for call in handle.write.call_args_list)

            self.assertIn(self.text_rep_val, html_content)
            self.assertIn(self.ascii_rep_val, html_content)
            self.assertIn("<html>", html_content)

    def test_export_html_report_raises_exporter_error_on_exception(self):
        err_msg = uuid.uuid4().hex
        self.mock_visualizer.render_text.side_effect = Exception(err_msg)

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_html_report(self.html_output_path)
        self.assertIn(err_msg, str(ctx.exception))

    def test_export_stream_to_json_success(self):
        stream_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_digest.export_digest_stream.return_value = stream_payload

        m_open = mock_open()
        with patch("builtins.open", m_open):
            res_path = self.exporter.export_stream_to_json(self.stream_id, self.output_path)
            self.assertEqual(res_path, self.output_path)
            self.mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)

            handle = m_open()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed = json.loads(written_data)
            self.assertEqual(parsed, stream_payload)

    def test_export_stream_to_json_raises_exporter_error(self):
        err_msg = uuid.uuid4().hex
        self.mock_digest.export_digest_stream.side_effect = Exception(err_msg)

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_stream_to_json(self.stream_id, self.output_path)
        self.assertIn(err_msg, str(ctx.exception))

    def test_export_to_json_adapter_success(self):
        adapter_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_visualizer.digest = adapter_data

        m_open = mock_open()
        with patch("builtins.open", m_open):
            res_path = self.exporter.export_to_json(self.output_path)
            self.assertEqual(res_path, self.output_path)

            handle = m_open()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed = json.loads(written_data)
            self.assertEqual(parsed, adapter_data)

    def test_export_to_json_adapter_empty_when_no_digest(self):
        if hasattr(self.mock_visualizer, "digest"):
            del self.mock_visualizer.digest

        m_open = mock_open()
        with patch("builtins.open", m_open):
            self.exporter.export_to_json(self.output_path)
            handle = m_open()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed = json.loads(written_data)
            self.assertEqual(parsed, {})

    def test_export_to_html_adapter_success(self):
        adapter_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_visualizer.digest = adapter_data

        m_open = mock_open()
        with patch("builtins.open", m_open):
            res_path = self.exporter.export_to_html(self.html_output_path)
            self.assertEqual(res_path, self.html_output_path)

            handle = m_open()
            html_content = "".join(call.args[0] for call in handle.write.call_args_list)
            self.assertIn("<html>", html_content)
            self.assertIn(json.dumps(adapter_data), html_content)

    def test_already_digest_exporter_error_passes_through(self):
        err_msg = uuid.uuid4().hex
        custom_ex = DigestExporterError(err_msg)
        self.mock_visualizer.get_summary_metrics.side_effect = custom_ex

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_json_report(self.output_path)
        self.assertEqual(str(ctx.exception), err_msg)