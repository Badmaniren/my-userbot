import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer, market_portfolio_stress_audit_visualizer
from skills.market_portfolio_stress_scenario_matrix_evaluator import market_portfolio_stress_scenario_matrix_evaluator
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.adaptive_risk_score = round(random.uniform(10.0, 95.0), 2)
        self.tail_risk_metrics = {"var_99": round(random.uniform(-0.15, -0.02), 4), "cvar_99": round(random.uniform(-0.25, -0.05), 4)}
        
        self.dependencies = {
            "market_portfolio_stress_scenario_matrix_evaluator": market_portfolio_stress_scenario_matrix_evaluator,
            "market_portfolio_stress_monte_carlo_engine": market_portfolio_stress_monte_carlo_engine
        }
        self.visualizer = MarketPortfolioStressAuditVisualizer(**self.dependencies)

    def test_graphical_visualization_integration(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": self.adaptive_risk_score,
            "tail_risk_metrics": self.tail_risk_metrics,
            "stream_payload": {"recovery_steps": random.randint(3, 10)}
        }

        result = self.visualizer.visualize(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("layout"), "graphical")
        self.assertEqual(result.get("adaptive_risk_score"), self.adaptive_risk_score)
        self.assertEqual(result.get("tail_risk_metrics"), self.tail_risk_metrics)
        self.assertIn("stream_payload", result)

    def test_text_summary_visualization_integration(self):
        payload = {
            "report_id": self.portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.adaptive_risk_score,
            "export_to_text_report": True
        }

        result = market_portfolio_stress_audit_visualizer(payload)

        self.assertIsInstance(result, str)
        self.assertIn(self.portfolio_id, result)
        self.assertIn(str(self.adaptive_risk_score), result)
        self.assertIn("Exported to text report successfully", result)

if __name__ == "__main__":
    unittest.main()