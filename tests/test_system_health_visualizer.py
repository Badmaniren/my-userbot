import unittest
from unittest.mock import patch
import uuid
import random
import io
import os
from skills.system_health_visualizer import SystemHealthVisualizer, system_health_visualizer

class TestSystemHealthVisualizer(unittest.TestCase):
    def test_visualize_critical_metrics_success(self):
        sys_id = uuid.uuid4().hex
        random_metric_key = uuid.uuid4().hex
        random_metric_val = random.randint(1, 1000)
        mock_gateway_data = {random_metric_key: random_metric_val}

        with patch("skills.system_health_visualizer.SystemHealthAggregator") as mock_agg_cls, \
             patch("skills.system_health_visualizer.SystemHealthMonitoringGateway") as mock_gw_cls:
            
            mock_agg_instance = mock_agg_cls.return_value
            mock_gw_instance = mock_gw_cls.return_value
            mock_gw_instance.fetch_metrics.return_value = mock_gateway_data

            visualizer = SystemHealthVisualizer()
            result = visualizer.visualize_critical_metrics(sys_id)

            mock_agg_instance.aggregate.assert_called_once_with(sys_id)
            mock_gw_instance.fetch_metrics.assert_called_once_with(sys_id)
            self.assertEqual(result.get(random_metric_key), random_metric_val)
            self.assertEqual(result.get("chart_rendering"), "success")

    def test_visualize_critical_metrics_non_dict(self):
        sys_id = uuid.uuid4().hex

        with patch("skills.system_health_visualizer.SystemHealthAggregator") as mock_agg_cls, \
             patch("skills.system_health_visualizer.SystemHealthMonitoringGateway") as mock_gw_cls:
            
            mock_gw_instance = mock_gw_cls.return_value
            mock_gw_instance.fetch_metrics.return_value = [uuid.uuid4().hex, uuid.uuid4().hex]

            visualizer = SystemHealthVisualizer()
            result = visualizer.visualize_critical_metrics(sys_id)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("chart_rendering"), "success")

    def test_build_realtime_status_graph_non_empty(self):
        sys_id = uuid.uuid4().hex
        random_payload = uuid.uuid4().hex.encode('utf-8')

        with patch("skills.system_health_visualizer.SystemHealthTelemetryCollector") as mock_col_cls:
            mock_col_instance = mock_col_cls.return_value
            mock_stream = io.BytesIO(random_payload)
            mock_col_instance.stream_telemetry.return_value = mock_stream

            visualizer = SystemHealthVisualizer()
            result = visualizer.build_realtime_status_graph(sys_id)

            mock_col_instance.stream_telemetry.assert_called_once_with(sys_id)
            self.assertIn(f"node_{sys_id}", result.get("nodes", []))
            self.assertIn("edges", result)

    def test_build_realtime_status_graph_empty(self):
        sys_id = uuid.uuid4().hex

        with patch("skills.system_health_visualizer.SystemHealthTelemetryCollector") as mock_col_cls:
            mock_col_instance = mock_col_cls.return_value
            mock_stream = io.BytesIO(b"")
            mock_col_instance.stream_telemetry.return_value = mock_stream

            visualizer = SystemHealthVisualizer()
            result = visualizer.build_realtime_status_graph(sys_id)

            self.assertEqual(result.get("status"), "EMPTY_STREAM")
            self.assertEqual(result.get("nodes"), [])

    def test_system_health_visualizer_function_basic(self):
        node_id = uuid.uuid4().hex
        metric_key = uuid.uuid4().hex
        metric_val = random.randint(10, 500)
        payload = {
            "node_id": node_id,
            "metrics": {metric_key: metric_val}
        }

        res = system_health_visualizer(payload)
        self.assertEqual(res.get("target_node"), node_id)
        self.assertIn(metric_key, res.get("rendered_metrics", ""))

    def test_system_health_visualizer_with_output_path(self):
        node_id = uuid.uuid4().hex
        dir_name = uuid.uuid4().hex
        file_name = f"{uuid.uuid4().hex}.txt"
        output_path = os.path.join(dir_name, file_name)

        payload = {
            "node_id": node_id,
            "metrics": {uuid.uuid4().hex: random.randint(1, 100)}
        }

        try:
            res = system_health_visualizer(payload, output_path=output_path)
            self.assertEqual(res.get("target_node"), node_id)
            self.assertTrue(os.path.exists(output_path))
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertEqual(content, "CHART_DATA")
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
            if os.path.exists(dir_name):
                os.rmdir(dir_name)