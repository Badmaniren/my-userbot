import unittest
from unittest.mock import patch, mock_open, MagicMock
import uuid
import random
import json
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.output_path = f"{uuid.uuid4().hex}.json"
        self.html_output_path = f"{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex

        self.mock_stability_digest = MagicMock()
        self.mock_anomaly_visualizer = MagicMock()

        self.exporter = DigestExporter(
            stability_digest=self.mock_stability_digest,
            anomaly_visualizer=self.mock_anomaly_visualizer
        )

    def test_export_json_report_success(self):
        random_metric_key = uuid.uuid4().hex
        random_metric_value = random.randint(1, 1000)
        random_text = uuid.uuid4().hex
        random_ascii = uuid.uuid4().hex

        self.mock_anomaly_visualizer.get_summary_metrics.return_value = {random_metric_key: random_metric_value}
        self.mock_anomaly_visualizer.render_text.return_value = random_text
        self.mock_anomaly_visualizer.render_ascii_correlation_graph.return_value = random_ascii

        m_open = mock_open()
        with patch("builtins.open", m_open):
            result = self.exporter.export_json_report(self.output_path)

        self.assertEqual(result, self.output_path)
        m_open.assert_called_once_with(self.output_path, 'w', encoding='utf-8')

        handle = m_open()
        written_data = "".join(call.args[0] for call in handle.write.mock_calls)
        parsed_data = json.loads(written_data)

        self.assertEqual(parsed_data.get(random_metric_key), random_metric_value)
        self.assertEqual(parsed_data.get('text_report'), random_text)
        self.assertEqual(parsed_data.get('ascii_graph'), random_ascii)

    def test_export_json_report_handles_non_dict_metrics(self):
        self.mock_anomaly_visualizer.get_summary_metrics.return_value = uuid.uuid4().hex
        self.mock_anomaly_visualizer.render_text.return_value = uuid.uuid4().hex
        self.mock_anomaly_visualizer.render_ascii_correlation_graph.return_value = uuid.uuid4().hex

        m_open = mock_open()
        with patch("builtins.open", m_open):
            self.exporter.export_json_report(self.output_path)

        handle = m_open()
        written_data = "".join(call.args[0] for call in handle.write.mock_calls)
        parsed_data = json.loads(written_data)
        self.assertIn('text_report', parsed_data)
        self.assertIn('ascii_graph', parsed_data)

    def test_export_json_report_raises_exporter_error_on_exception(self):
        self.mock_anomaly_visualizer.get_summary_metrics.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(self.output_path)

    def test_export_html_report_success(self):
        random_metric_val = uuid.uuid4().hex
        random_text = uuid.uuid4().hex
        random_ascii = uuid.uuid4().hex

        self.mock_anomaly_visualizer.get_summary_metrics.return_value = random_metric_val
        self.mock_anomaly_visualizer.render_text.return_value = random_text
        self.mock_anomaly_visualizer.render_ascii_correlation_graph.return_value = random_ascii

        m_open = mock_open()
        with patch("builtins.open", m_open):
            result = self.exporter.export_html_report(self.html_output_path)

        self.assertEqual(result, self.html_output_path)
        m_open.assert_called_once_with(self.html_output_path, 'w', encoding='utf-8')

        handle = m_open()
        written_data = "".join(call.args[0] for call in handle.write.mock_calls)
        self.assertIn(str(random_metric_val), written_data)
        self.assertIn(random_text, written_data)
        self.assertIn(random_ascii, written_data)

    def test_export_html_report_raises_exporter_error_on_exception(self):
        self.mock_anomaly_visualizer.render_text.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_html_report(self.html_output_path)

    def test_export_stream_to_json_success(self):
        random_stream_key = uuid.uuid4().hex
        random_stream_val = uuid.uuid4().hex
        self.mock_stability_digest.export_digest_stream.return_value = {random_stream_key: random_stream_val}

        m_open = mock_open()
        with patch("builtins.open", m_open):
            result = self.exporter.export_stream_to_json(self.stream_id, self.output_path)

        self.assertEqual(result, self.output_path)
        self.mock_stability_digest.export_digest_stream.assert_called_once_with(self.stream_id)

        handle = m_open()
        written_data = "".join(call.args[0] for call in handle.write.mock_calls)
        parsed_data = json.loads(written_data)
        self.assertEqual(parsed_data.get(random_stream_key), random_stream_val)

    def test_export_stream_to_json_raises_exporter_error_on_exception(self):
        self.mock_stability_digest.export_digest_stream.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_stream_to_json(self.stream_id, self.output_path)

    def test_export_to_json_adapter_success(self):
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        self.mock_anomaly_visualizer.digest = {random_key: random_val}

        m_open = mock_open()
        with patch("builtins.open", m_open):
            result = self.exporter.export_to_json(self.output_path)

        self.assertEqual(result, self.output_path)
        handle = m_open()
        written_data = "".join(call.args[0] for call in handle.write.mock_calls)
        parsed_data = json.loads(written_data)
        self.assertEqual(parsed_data.get(random_key), random_val)

    def test_export_to_json_adapter_fallback_no_digest(self):
        if hasattr(self.mock_anomaly_visualizer, 'digest'):
            del self.mock_anomaly_visualizer.digest

        m_open = mock_open()
        with patch("builtins.open", m_open):
            result = self.exporter.export_to_json(self.output_path)

        self.assertEqual(result, self.output_path)
        handle = m_open()
        written_data = "".join(call.args[0] for call in handle.write.mock_calls)
        parsed_data = json.loads(written_data)
        self.assertEqual(parsed_data, {})

    def test_export_to_html_adapter_success(self):
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        self.mock_anomaly_visualizer.digest = {random_key: random_val}

        m_open = mock_open()
        with patch("builtins.open", m_open):
            result = self.exporter.export_to_html(self.html_output_path)

        self.assertEqual(result, self.html_output_path)
        handle = m_open()
        written_data = "".join(call.args[0] for call in handle.write.mock_calls)
        self.assertIn(random_key, written_data)
        self.assertIn(random_val, written_data)

    def test_export_to_html_adapter_fallback_no_digest(self):
        if hasattr(self.mock_anomaly_visualizer, 'digest'):
            del self.mock_anomaly_visualizer.digest

        m_open = mock_open()
        with patch("builtins.open", m_open):
            result = self.exporter.export_to_html(self.html_output_path)

        self.assertEqual(result, self.html_output_path)
        handle = m_open()
        written_data = "".join(call.args[0] for call in handle.write.mock_calls)
        self.assertIn("<html>", written_data)


if __name__ == '__main__':
    unittest.main()