import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import (
    MarketPortfolioStressAuditVisualizer,
    market_portfolio_stress_audit_visualizer,
)
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.market_portfolio_liquidity_scenario_analyzer import market_portfolio_liquidity_scenario_analyzer


class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = f"port-{uuid.uuid4()}"
        self.adaptive_risk_score = round(random.uniform(10.0, 99.9), 2)
        self.monte_carlo_runs = random.randint(100, 1000)

        self.mc_payload = {
            "portfolio_id": self.portfolio_id,
            "simulations": self.monte_carlo_runs,
            "confidence_level": 0.95
        }
        self.liquidity_payload = {
            "portfolio_id": self.portfolio_id,
            "shock_factor": random.uniform(0.1, 0.5)
        }

    def test_integration_stress_audit_pipeline(self):
        mc_result = market_portfolio_stress_monte_carlo_engine(self.mc_payload)
        liquidity_result = market_portfolio_liquidity_scenario_analyzer(self.liquidity_payload)

        visualizer_payload = {
            "portfolio_id": self.portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": self.adaptive_risk_score,
            "tail_risk_metrics": {
                "monte_carlo": mc_result,
                "liquidity_shock": liquidity_result
            },
            "stream_payload": {
                "active_runs": self.monte_carlo_runs
            }
        }

        visualizer_instance = MarketPortfolioStressAuditVisualizer(
            db_storage=None,
            market_portfolio_stress_monte_carlo_engine=market_portfolio_stress_monte_carlo_engine,
            market_portfolio_liquidity_scenario_analyzer=market_portfolio_liquidity_scenario_analyzer
        )

        result_obj = visualizer_instance.visualize(visualizer_payload)
        result_func = market_portfolio_stress_audit_visualizer(visualizer_payload)

        self.assertEqual(result_obj["portfolio_id"], self.portfolio_id)
        self.assertEqual(result_func["portfolio_id"], self.portfolio_id)
        self.assertEqual(result_obj["adaptive_risk_score"], self.adaptive_risk_score)
        self.assertIn("tail_risk_metrics", result_obj)
        self.assertIn("monte_carlo", result_obj["tail_risk_metrics"])
        self.assertIn("liquidity_shock", result_obj["tail_risk_metrics"])

    def test_integration_text_summary_format(self):
        visualizer_payload = {
            "report_id": self.portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": self.adaptive_risk_score,
            "export_to_text_report": True
        }

        result = market_portfolio_stress_audit_visualizer(visualizer_payload)
        
        self.assertIsInstance(result, str)
        self.assertIn(self.portfolio_id, result)
        self.assertIn(str(self.adaptive_risk_score), result)
        self.assertIn("Exported to text report successfully.", result)


if __name__ == "__main__":
    unittest.main()