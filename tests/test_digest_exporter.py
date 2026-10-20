import unittest
from unittest.mock import patch, mock_open, MagicMock
import uuid
import random
import string
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.random_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        self.random_html_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.html"
        self.random_stream_id = uuid.uuid4().hex

        self.mock_visualizer = MagicMock()
        self.mock_digest = MagicMock()

        self.exporter = DigestExporter(
            stability_digest=self.mock_digest,
            anomaly_visualizer=self.mock_visualizer
        )

    def test_export_json_report_success(self):
        expected_metric_key = uuid.uuid4().hex
        expected_metric_val = random.randint(1, 1000)
        expected_text = uuid.uuid4().hex
        expected_ascii = uuid.uuid4().hex

        self.mock_visualizer.get_summary_metrics.return_value = {expected_metric_key: expected_metric_val}
        self.mock_visualizer.render_text.return_value = expected_text
        self.mock_visualizer.render_ascii_correlation_graph.return_value = expected_ascii

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_json_report(self.random_path)

            self.assertEqual(result_path, self.random_path)
            mocked_file.assert_called_once_with(self.random_path, 'w', encoding='utf-8')

    def test_export_json_report_non_dict_metrics(self):
        self.mock_visualizer.get_summary_metrics.return_value = [random.randint(1, 50)]
        expected_text = uuid.uuid4().hex
        expected_ascii = uuid.uuid4().hex

        self.mock_visualizer.render_text.return_value = expected_text
        self.mock_visualizer.render_ascii_correlation_graph.return_value = expected_ascii

        with patch("builtins.open", mock_open()):
            result_path = self.exporter.export_json_report(self.random_path)
            self.assertEqual(result_path, self.random_path)

    def test_export_json_report_raises_exporter_error(self):
        self.mock_visualizer.get_summary_metrics.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(self.random_path)

    def test_export_html_report_success(self):
        expected_metric = uuid.uuid4().hex
        expected_text = uuid.uuid4().hex
        expected_ascii = uuid.uuid4().hex

        self.mock_visualizer.get_summary_metrics.return_value = expected_metric
        self.mock_visualizer.render_text.return_value = expected_text
        self.mock_visualizer.render_ascii_correlation_graph.return_value = expected_ascii

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_html_report(self.random_html_path)

            self.assertEqual(result_path, self.random_html_path)
            mocked_file.assert_called_once_with(self.random_html_path, 'w', encoding='utf-8')

    def test_export_html_report_raises_exporter_error(self):
        self.mock_visualizer.get_summary_metrics.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_html_report(self.random_html_path)

    def test_export_stream_to_json_success(self):
        expected_stream_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_digest.export_digest_stream.return_value = expected_stream_data

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_stream_to_json(self.random_stream_id, self.random_path)

            self.assertEqual(result_path, self.random_path)
            self.mock_digest.export_digest_stream.assert_called_once_with(self.random_stream_id)
            mocked_file.assert_called_once_with(self.random_path, 'w', encoding='utf-8')

    def test_export_stream_to_json_raises_exporter_error(self):
        self.mock_digest.export_digest_stream.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_stream_to_json(self.random_stream_id, self.random_path)

    def test_export_to_json_adapter_with_digest(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        self.mock_visualizer.digest = {rand_key: rand_val}

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_to_json(self.random_path)

            self.assertEqual(result_path, self.random_path)
            mocked_file.assert_called_once_with(self.random_path, 'w', encoding='utf-8')

    def test_export_to_json_adapter_without_digest(self):
        self.exporter.visualizer = None

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_to_json(self.random_path)

            self.assertEqual(result_path, self.random_path)
            mocked_file.assert_called_once_with(self.random_path, 'w', encoding='utf-8')

    def test_export_to_json_adapter_raises_exporter_error(self):
        with patch("builtins.open", side_effect=Exception(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_json(self.random_path)

    def test_export_to_html_adapter_with_digest(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        self.mock_visualizer.digest = {rand_key: rand_val}

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_to_html(self.random_html_path)

            self.assertEqual(result_path, self.random_html_path)
            mocked_file.assert_called_once_with(self.random_html_path, 'w', encoding='utf-8')

    def test_export_to_html_adapter_without_digest(self):
        self.exporter.visualizer = MagicMock(spec=[])

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_to_html(self.random_html_path)

            self.assertEqual(result_path, self.random_html_path)
            mocked_file.assert_called_once_with(self.random_html_path, 'w', encoding='utf-8')

    def test_export_to_html_adapter_raises_exporter_error(self):
        with patch("builtins.open", side_effect=Exception(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_html(self.random_html_path)