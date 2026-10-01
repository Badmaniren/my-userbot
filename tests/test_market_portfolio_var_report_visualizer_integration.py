import unittest
import os
import io
import uuid
import random
from skills.market_portfolio_var_report_visualizer import (
    MarketPortfolioVarReportVisualizer,
    market_portfolio_var_report_visualizer
)

class RealDummyDbStorage:
    def fetch_var_data(self, portfolio_id: str) -> dict:
        return {"portfolio_id": portfolio_id}

class RealDummyExtractor:
    def __init__(self, scenario: str, impact: float):
        self.scenario = scenario
        self.impact = impact

    def extract(self, stream_key: str) -> dict:
        return {"scenario": f"{self.scenario}_{stream_key}", "portfolio_impact": self.impact}

    def process(self, file_token: str):
        return io.BytesIO(f"data_{file_token}".encode('utf-8'))

class RealDummyAnomalyDetector:
    def scan(self, anomaly_id: str) -> dict:
        return {
            "anomaly_id": anomaly_id,
            "severity": "HIGH",
            "metric": "VaR_SPIKE"
        }

class RealDummyVisualizerV2:
    def export_bytes(self, anomaly_id: str) -> bytes:
        return f"bytes_{anomaly_id}".encode('utf-8')

class TestMarketPortfolioVarReportVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.output_path = f"test_var_report_{uuid.uuid4()}.png"
        self.stream_key = str(uuid.uuid4())
        self.anomaly_id = str(uuid.uuid4())
        self.file_token = str(uuid.uuid4())

        self.db_storage = RealDummyDbStorage()
        self.extractor_1 = RealDummyExtractor("Baseline_Scenario", random.uniform(-0.15, -0.01))
        self.extractor_2 = RealDummyExtractor("Heatmap", 0.0)
        self.anomaly_detector = RealDummyAnomalyDetector()
        self.visualizer_v2 = RealDummyVisualizerV2()

        self.visualizer_instance = MarketPortfolioVarReportVisualizer(
            db_storage=self.db_storage,
            extractor_tool_1790087207=self.extractor_1,
            extractor_tool_1790102839=self.extractor_2,
            market_anomaly_detector=self.anomaly_detector,
            market_portfolio_visualizer_v2=self.visualizer_v2
        )

    def tearDown(self):
        if os.path.exists(self.output_path):
            try:
                os.remove(self.output_path)
            except OSError:
                pass

    def test_generate_var_report_chart_integration(self):
        res_path = self.visualizer_instance.generate_var_report_chart(self.portfolio_id, self.output_path)
        self.assertEqual(res_path, self.output_path)
        self.assertTrue(os.path.exists(self.output_path))
        self.assertGreater(os.path.getsize(self.output_path), 0)

    def test_render_stress_test_table_integration(self):
        result_str = self.visualizer_instance.render_stress_test_table(self.stream_key)
        self.assertIn(self.stream_key, result_str)
        self.assertIn("Scenario: Baseline_Scenario", result_str)
        self.assertIn("Impact:", result_str)

    def test_build_anomaly_overlay_report_integration(self):
        report = self.visualizer_instance.build_anomaly_overlay_report(self.anomaly_id)
        self.assertEqual(report.get("anomaly_id"), self.anomaly_id)
        self.assertEqual(report.get("severity"), "HIGH")
        self.assertEqual(report.get("metric"), "VaR_SPIKE")
        self.assertEqual(report.get("visual_stream"), f"bytes_{self.anomaly_id}".encode('utf-8'))

    def test_export_var_heatmap_integration(self):
        stream = self.visualizer_instance.export_var_heatmap(self.file_token)
        self.assertIsInstance(stream, io.BytesIO)
        content = stream.getvalue().decode('utf-8')
        self.assertEqual(content, f"data_{self.file_token}")

    def test_functional_wrapper_integration(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "output_path": self.output_path
        }
        res = market_portfolio_var_report_visualizer(payload)
        self.assertEqual(res.get("portfolio_id"), self.portfolio_id)
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("file_path"), self.output_path)
        self.assertTrue(os.path.exists(self.output_path))

if __name__ == "__main__":
    unittest.main()