import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
from skills.digest_dashboard_generator import DigestDashboardGenerator, DigestDashboardGeneratorError


class TestDigestDashboardGenerator(unittest.TestCase):

    def setUp(self):
        self.random_digest = {str(uuid.uuid4()): random.randint(1, 100)}
        self.json_path = f"reports_{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        self.html_path = f"reports_{uuid.uuid4().hex}/{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex

    def test_init_with_defaults(self):
        with patch('skills.digest_dashboard_generator.AnomalyVisualizer') as mock_vis_cls, \
             patch('skills.digest_dashboard_generator.DigestExporter') as mock_exp_cls:

            mock_vis_instance = MagicMock()
            mock_exp_instance = MagicMock()
            mock_vis_cls.return_value = mock_vis_instance
            mock_exp_cls.return_value = mock_exp_instance

            generator = DigestDashboardGenerator(stability_digest=self.random_digest)

            mock_vis_cls.assert_called_once_with(digest=self.random_digest)
            mock_exp_cls.assert_called_once_with(stability_digest=self.random_digest, anomaly_visualizer=mock_vis_instance)
            self.assertEqual(generator.digest_data, self.random_digest)

    def test_init_with_custom_injections(self):
        mock_vis = MagicMock()
        mock_exp = MagicMock()

        generator = DigestDashboardGenerator(
            stability_digest=self.random_digest,
            anomaly_visualizer=mock_vis,
            digest_exporter=mock_exp
        )

        self.assertEqual(generator.visualizer, mock_vis)
        self.assertEqual(generator.exporter, mock_exp)

    def test_generate_dashboard_success(self):
        mock_vis = MagicMock()
        mock_exp = MagicMock()

        expected_json_res = f"path_{uuid.uuid4().hex}.json"
        expected_html_res = f"path_{uuid.uuid4().hex}.html"

        mock_exp.export_to_json.return_value = expected_json_res
        mock_exp.export_to_html.return_value = expected_html_res

        generator = DigestDashboardGenerator(
            stability_digest=self.random_digest,
            anomaly_visualizer=mock_vis,
            digest_exporter=mock_exp
        )

        with patch('os.makedirs') as mock_makedirs, \
             patch('os.path.exists', return_value=False) as mock_exists:

            result = generator.generate_dashboard(self.json_path, self.html_path)

            mock_exp.export_to_json.assert_called_once_with(self.json_path)
            mock_exp.export_to_html.assert_called_once_with(self.html_path)
            self.assertEqual(result, {
                'json_report': expected_json_res,
                'html_report': expected_html_res
            })
            self.assertTrue(mock_makedirs.called)

    def test_generate_dashboard_handles_exception(self):
        mock_vis = MagicMock()
        mock_exp = MagicMock()

        random_error_msg = uuid.uuid4().hex
        mock_exp.export_to_json.side_effect = Exception(random_error_msg)

        generator = DigestDashboardGenerator(
            stability_digest=self.random_digest,
            anomaly_visualizer=mock_vis,
            digest_exporter=mock_exp
        )

        with patch('os.makedirs'):
            with self.assertRaises(DigestDashboardGeneratorError) as ctx:
                generator.generate_dashboard(self.json_path, self.html_path)

            self.assertIn(random_error_msg, str(ctx.exception))

    def test_get_metrics_summary(self):
        mock_vis = MagicMock()
        expected_metrics = {uuid.uuid4().hex: random.randint(10, 500)}
        mock_vis.get_summary_metrics.return_value = expected_metrics

        generator = DigestDashboardGenerator(
            stability_digest=self.random_digest,
            anomaly_visualizer=mock_vis
        )

        metrics = generator.get_metrics_summary()
        mock_vis.get_summary_metrics.assert_called_once()
        self.assertEqual(metrics, expected_metrics)

    def test_render_ascii_graph(self):
        mock_vis = MagicMock()
        expected_graph = f"graph_{uuid.uuid4().hex}"
        mock_vis.render_ascii_correlation_graph.return_value = expected_graph

        generator = DigestDashboardGenerator(
            stability_digest=self.random_digest,
            anomaly_visualizer=mock_vis
        )

        graph = generator.render_ascii_graph()
        mock_vis.render_ascii_correlation_graph.assert_called_once()
        self.assertEqual(graph, expected_graph)

    def test_export_stream(self):
        mock_exp = MagicMock()
        expected_export_path = f"stream_{uuid.uuid4().hex}.json"
        mock_exp.export_stream_to_json.return_value = expected_export_path

        generator = DigestDashboardGenerator(
            stability_digest=self.random_digest,
            digest_exporter=mock_exp
        )

        res = generator.export_stream(self.stream_id, self.json_path)
        mock_exp.export_stream_to_json.assert_called_once_with(self.stream_id, self.json_path)
        self.assertEqual(res, expected_export_path)

    def test_generate_html_dashboard(self):
        mock_exp = MagicMock()
        expected_html_path = f"html_{uuid.uuid4().hex}.html"
        mock_exp.export_to_html.return_value = expected_html_path

        generator = DigestDashboardGenerator(
            stability_digest=self.random_digest,
            digest_exporter=mock_exp
        )

        with patch('os.makedirs') as mock_makedirs, \
             patch('os.path.exists', return_value=False):

            res = generator.generate_html_dashboard(self.html_path)
            mock_exp.export_to_html.assert_called_once_with(self.html_path)
            self.assertEqual(res, expected_html_path)
            self.assertTrue(mock_makedirs.called)

    def test_generate_json_dashboard(self):
        mock_exp = MagicMock()
        expected_json_path = f"json_{uuid.uuid4().hex}.json"
        mock_exp.export_to_json.return_value = expected_json_path

        generator = DigestDashboardGenerator(
            stability_digest=self.random_digest,
            digest_exporter=mock_exp
        )

        with patch('os.makedirs') as mock_makedirs, \
             patch('os.path.exists', return_value=True):

            res = generator.generate_json_dashboard(self.json_path)
            mock_exp.export_to_json.assert_called_once_with(self.json_path)
            self.assertEqual(res, expected_json_path)
            mock_makedirs.assert_not_called()


if __name__ == '__main__':
    unittest.main()