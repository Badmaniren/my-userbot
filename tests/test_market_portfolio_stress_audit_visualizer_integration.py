import unittest
import uuid
import random
from skills.market_portfolio_stress_audit_visualizer import MarketPortfolioStressAuditVisualizer, market_portfolio_stress_audit_visualizer
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_report_generator import market_report_generator

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    def test_stress_audit_visualizer_integration(self):
        rand_id = f"port_{uuid.uuid4().hex[:8]}"
        risk_score = round(random.uniform(10.0, 99.9), 2)
        
        sim_payload = {
            "portfolio_id": rand_id,
            "scenario": "market_crash",
            "intensity": random.choice([0.1, 0.25, 0.5])
        }
        sim_result = market_portfolio_scenario_simulator(sim_payload)
        
        report_payload = {
            "report_id": rand_id,
            "simulation_data": sim_result,
            "format": "detailed"
        }
        report_result = market_report_generator(report_payload)
        
        visualizer_instance = MarketPortfolioStressAuditVisualizer(
            market_portfolio_scenario_simulator=market_portfolio_scenario_simulator,
            market_report_generator=market_report_generator
        )
        
        payload = {
            "portfolio_id": rand_id,
            "format": "graphical",
            "adaptive_risk_score": risk_score,
            "export_to_text_report": True,
            "simulation_ref": sim_result,
            "report_ref": report_result
        }
        
        res_func = market_portfolio_stress_audit_visualizer(payload)
        res_class = visualizer_instance.visualize(payload)
        
        self.assertEqual(res_func, res_class)
        self.assertEqual(res_func["portfolio_id"], rand_id)
        self.assertEqual(res_func["adaptive_risk_score"], risk_score)
        self.assertEqual(res_func["status"], "success")
        self.assertEqual(res_func["layout"], "graphical")

if __name__ == "__main__":
    unittest.main()