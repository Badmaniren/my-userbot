import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer, market_portfolio_stress_audit_visualizer
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.market_report_generator import market_report_generator

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def test_end_to_end_stress_audit_visualization(self):
        portfolio_id = f"port-{uuid.uuid4()}"
        adaptive_score = round(random.uniform(1.0, 99.9), 2)
        
        sim_payload = {
            "portfolio_id": portfolio_id,
            "scenario": "black_swan",
            "intensity": random.choice([1.5, 2.0, 3.0])
        }
        sim_result = market_portfolio_scenario_simulator(sim_payload)

        mc_payload = {
            "portfolio_id": portfolio_id,
            "simulations": random.randint(100, 1000),
            "simulation_data": sim_result
        }
        mc_result = market_portfolio_stress_monte_carlo_engine(mc_payload)

        visualizer = MarketPortfolioStressAuditVisualizer(
            market_portfolio_scenario_simulator=market_portfolio_scenario_simulator,
            market_portfolio_stress_monte_carlo_engine=market_portfolio_stress_monte_carlo_engine,
            market_report_generator=market_report_generator
        )

        vis_payload = {
            "portfolio_id": portfolio_id,
            "format": "text_summary",
            "adaptive_risk_score": adaptive_score,
            "export_to_text_report": True,
            "monte_carlo_metrics": mc_result
        }
        
        output_summary = visualizer.visualize(vis_payload)
        
        self.assertIn(portfolio_id, output_summary)
        self.assertIn(str(adaptive_score), output_summary)
        self.assertIn("Exported to text report successfully", output_summary)
        
        vis_payload_graph = {
            "report_id": portfolio_id,
            "format": "graphical",
            "adaptive_risk_score": adaptive_score
        }
        output_graph = market_portfolio_stress_audit_visualizer(vis_payload_graph)
        
        self.assertEqual(output_graph.get("portfolio_id"), portfolio_id)
        self.assertEqual(output_graph.get("status"), "success")
        self.assertEqual(output_graph.get("layout"), "graphical")
        self.assertEqual(output_graph.get("adaptive_risk_score"), adaptive_score)

if __name__ == "__main__":
    unittest.main()