import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import os
import sys

class MockMatplotlibFigure:
    def __init__(self, *args, **kwargs):
        pass

class MockMatplotlibPyplot:
    def figure(self, *args, **kwargs):
        return MockMatplotlibFigure()
    def title(self, *args, **kwargs):
        pass
    def savefig(self, output_path=None, *args, **kwargs):
        if output_path and isinstance(output_path, str):
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(b"fake_chart_bytes")
    def close(self, *args, **kwargs):
        pass

sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.pyplot'] = MockMatplotlibPyplot()

from skills.market_portfolio_var_report_visualizer import (
    MarketPortfolioVarReportVisualizer,
    market_portfolio_var_report_visualizer
)


class TestMarketPortfolioVarReportVisualizer(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.extractor_1 = MagicMock()
        self.extractor_2 = MagicMock()
        self.extractor_3 = MagicMock()
        self.extractor_4 = MagicMock()
        self.anomaly_detector = MagicMock()
        self.visualizer_v2 = MagicMock()

        self.visualizer = MarketPortfolioVarReportVisualizer(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2,
            extractor_tool_1790262909=self.extractor_3,
            extractor_tool_1790621808=self.extractor_4,
            market_anomaly_detector=self.anomaly_detector,
            market_portfolio_visualizer_v2=self.visualizer_v2
        )

    def test_generate_var_report_chart(self):
        portfolio_id = uuid.uuid4().hex
        output_path = f"{uuid.uuid4().hex}.png"
        expected_data = {"portfolio_id": portfolio_id}
        self.db_storage.fetch_var_data.return_value = expected_data

        result = self.visualizer.generate_var_report_chart(portfolio_id, output_path)

        self.db_storage.fetch_var_data.assert_called_once_with(portfolio_id)
        self.assertEqual(result, output_path)

    def test_render_stress_test_table(self):
        stream_key = uuid.uuid4().hex
        scenario = f"scenario_{uuid.uuid4().hex[:6]}"
        impact = round(random.uniform(-100.0, 0.0), 2)

        self.extractor_1.extract.return_value = {
            "scenario": scenario,
            "portfolio_impact": impact
        }

        result = self.visualizer.render_stress_test_table(stream_key)

        self.extractor_1.extract.assert_called_once_with(stream_key)
        self.assertIn(scenario, result)
        self.assertIn(str(impact), result)

    def test_build_anomaly_overlay_report(self):
        anomaly_id = uuid.uuid4().hex
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        metric = uuid.uuid4().hex
        visual_bytes = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))

        self.anomaly_detector.scan.return_value = {
            "anomaly_id": anomaly_id,
            "severity": severity,
            "metric": metric
        }
        self.visualizer_v2.export_bytes.return_value = visual_bytes

        result = self.visualizer.build_anomaly_overlay_report(anomaly_id)

        self.anomaly_detector.scan.assert_called_once_with(anomaly_id)
        self.visualizer_v2.export_bytes.assert_called_once_with(anomaly_id)

        self.assertEqual(result["anomaly_id"], anomaly_id)
        self.assertEqual(result["severity"], severity)
        self.assertEqual(result["metric"], metric)
        self.assertEqual(result["visual_stream"], visual_bytes)

    def test_export_var_heatmap(self):
        file_token = uuid.uuid4().hex
        expected_io = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        self.extractor_2.process.return_value = expected_io

        result = self.visualizer.export_var_heatmap(file_token)

        self.extractor_2.process.assert_called_once_with(file_token)
        self.assertEqual(result, expected_io)


class TestMarketPortfolioVarReportVisualizerIntegration(unittest.TestCase):

    def test_market_portfolio_var_report_visualizer_function(self):
        portfolio_id = uuid.uuid4().hex
        output_path = f"{uuid.uuid4().hex}.png"
        payload = {
            "portfolio_id": portfolio_id,
            "output_path": output_path
        }

        result = market_portfolio_var_report_visualizer(payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("file_path"), output_path)
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass

    def test_market_portfolio_var_report_visualizer_default_path(self):
        portfolio_id = uuid.uuid4().hex
        payload = {
            "portfolio_id": portfolio_id
        }

        result = market_portfolio_var_report_visualizer(payload)

        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("file_path"), "var_report.png")
        if os.path.exists("var_report.png"):
            try:
                os.remove("var_report.png")
            except OSError:
                pass