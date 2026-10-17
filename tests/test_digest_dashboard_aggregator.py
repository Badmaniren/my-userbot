import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.digest_dashboard_aggregator import DigestDashboardAggregator, DigestDashboardAggregatorError
from skills.digest_exporter import DigestExporterError
from skills.anomaly_visualizer import AnomalyVisualizerError


class TestDigestDashboardAggregator(unittest.TestCase):

    def setUp(self):
        self.stability_digest_mock = MagicMock()
        self.anomaly_visualizer_mock = MagicMock()
        self.aggregator = DigestDashboardAggregator(
            stability_digest=self.stability_digest_mock,
            anomaly_visualizer=self.anomaly_visualizer_mock
        )

    def test_init_and_composition(self):
        rand_digest = MagicMock()
        rand_visualizer = MagicMock()
        instance = DigestDashboardAggregator(
            stability_digest=rand_digest,
            anomaly_visualizer=rand_visualizer
        )
        self.assertEqual(instance.stability_digest, rand_digest)
        self.assertEqual(instance.anomaly_visualizer, rand_visualizer)

    def test_aggregate_operator_dashboard_success(self):
        rand_summary = {
            uuid.uuid4().hex: random.randint(100, 999),
            uuid.uuid4().hex: uuid.uuid4().hex
        }
        rand_graph = "".join(random.choices(string.ascii_letters + string.punctuation, k=50))
        rand_text = "".join(random.choices(string.ascii_letters + string.whitespace, k=100))

        self.anomaly_visualizer_mock.get_summary_metrics.return_value = rand_summary
        self.anomaly_visualizer_mock.render_ascii_correlation_graph.return_value = rand_graph
        self.anomaly_visualizer_mock.render_text.return_value = rand_text

        with patch('skills.digest_dashboard_aggregator.DigestExporter') as MockExporterClass:
            mock_exporter_instance = MockExporterClass.return_value
            rand_json_path = f"/tmp/{uuid.uuid4().hex}.json"
            rand_html_path = f"/tmp/{uuid.uuid4().hex}.html"
            mock_exporter_instance.export_json_report.return_value = rand_json_path
            mock_exporter_instance.export_html_report.return_value = rand_html_path

            result = self.aggregator.aggregate_operator_dashboard()

            self.assertIn("metrics", result)
            self.assertIn("ascii_graph", result)
            self.assertIn("text_render", result)
            self.assertIn("exported_json", result)
            self.assertIn("exported_html", result)

            self.assertEqual(result["metrics"], rand_summary)
            self.assertEqual(result["ascii_graph"], rand_graph)
            self.assertEqual(result["text_render"], rand_text)
            self.assertEqual(result["exported_json"], rand_json_path)
            self.assertEqual(result["exported_html"], rand_html_path)

            MockExporterClass.assert_called_once_with(
                stability_digest=self.stability_digest_mock,
                anomaly_visualizer=self.anomaly_visualizer_mock
            )
            mock_exporter_instance.export_json_report.assert_called_once()
            mock_exporter_instance.export_html_report.assert_called_once()

    def test_aggregate_operator_dashboard_exporter_error(self):
        self.anomaly_visualizer_mock.get_summary_metrics.return_value = {uuid.uuid4().hex: random.randint(1, 10)}
        self.anomaly_visualizer_mock.render_ascii_correlation_graph.return_value = uuid.uuid4().hex
        self.anomaly_visualizer_mock.render_text.return_value = uuid.uuid4().hex

        with patch('skills.digest_dashboard_aggregator.DigestExporter') as MockExporterClass:
            mock_exporter_instance = MockExporterClass.return_value
            rand_err_msg = uuid.uuid4().hex
            mock_exporter_instance.export_json_report.side_effect = DigestExporterError(rand_err_msg)

            with self.assertRaises(DigestDashboardAggregatorError) as ctx:
                self.aggregator.aggregate_operator_dashboard()

            self.assertIn(rand_err_msg, str(ctx.exception))

    def test_aggregate_operator_dashboard_visualizer_error(self):
        rand_err_msg = uuid.uuid4().hex
        self.anomaly_visualizer_mock.get_summary_metrics.side_effect = AnomalyVisualizerError(rand_err_msg)

        with self.assertRaises(DigestDashboardAggregatorError) as ctx:
            self.aggregator.aggregate_operator_dashboard()

        self.assertIn(rand_err_msg, str(ctx.exception))

    def test_export_stream_report_success(self):
        rand_stream_id = uuid.uuid4().hex
        rand_path = f"/var/log/{uuid.uuid4().hex}.json"

        with patch('skills.digest_dashboard_aggregator.DigestExporter') as MockExporterClass:
            mock_exporter_instance = MockExporterClass.return_value
            mock_exporter_instance.export_stream_to_json.return_value = rand_path

            res = self.aggregator.export_stream_report(rand_stream_id, rand_path)

            self.assertEqual(res, rand_path)
            mock_exporter_instance.export_stream_to_json.assert_called_once_with(
                stream_id=rand_stream_id,
                output_path=rand_path
            )

    def test_export_stream_report_failure(self):
        rand_stream_id = uuid.uuid4().hex
        rand_path = f"/var/log/{uuid.uuid4().hex}.json"
        rand_err = uuid.uuid4().hex

        with patch('skills.digest_dashboard_aggregator.DigestExporter') as MockExporterClass:
            mock_exporter_instance = MockExporterClass.return_value
            mock_exporter_instance.export_stream_to_json.side_effect = Exception(rand_err)

            with self.assertRaises(DigestDashboardAggregatorError) as ctx:
                self.aggregator.export_stream_report(rand_stream_id, rand_path)

            self.assertIn(rand_err, str(ctx.exception))

    def test_get_operator_summary_stream(self):
        rand_data = {
            uuid.uuid4().hex: uuid.uuid4().hex,
            "stream_score": random.random()
        }
        self.anomaly_visualizer_mock.visualize_digest.return_value = rand_data

        res = self.aggregator.get_operator_summary_stream(rand_data)

        self.assertEqual(res, rand_data)
        self.anomaly_visualizer_mock.visualize_digest.assert_called_once_with(rand_data)


if __name__ == '__main__':
    unittest.main()