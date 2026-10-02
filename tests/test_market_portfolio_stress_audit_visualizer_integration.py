import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_visualizer import market_portfolio_stress_audit_visualizer
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter
from skills.market_portfolio_stress_scenario_pipeline import market_portfolio_stress_scenario_pipeline
from skills.db_storage import db_storage

class TestMarketPortfolioStressAuditVisualizerIntegration(unittest.TestCase):
    
    def test_stress_audit_visualizer_end_to_end_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        scenario_id = f"scen_{uuid.uuid4().hex[:8]}"
        initial_capital = round(random.uniform(50000.0, 500000.0), 2)
        shock_percentage = round(random.uniform(-0.35, -0.05), 4)
        
        pipeline_input = {
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "capital": initial_capital,
            "shock": shock_percentage
        }
        
        scenario_result = market_portfolio_stress_scenario_pipeline(pipeline_input)
        self.assertIsNotNone(scenario_result)
        
        report_payload = {
            "portfolio_id": portfolio_id,
            "scenario_data": scenario_result,
            "audit_tag": uuid.uuid4().hex
        }
        
        stress_report = market_portfolio_stress_reporter(report_payload)
        self.assertIn("portfolio_id", stress_report)
        
        db_storage.save(f"audit_report_{portfolio_id}", stress_report)
        retrieved_report = db_storage.load(f"audit_report_{portfolio_id}")
        self.assertEqual(retrieved_report["portfolio_id"], portfolio_id)
        
        visualizer_payload = {
            "report_id": portfolio_id,
            "data": retrieved_report,
            "format": "text_summary"
        }
        
        visualization_output = market_portfolio_stress_audit_visualizer(visualizer_payload)
        
        self.assertIsNotNone(visualization_output)
        self.assertTrue(
            isinstance(visualization_output, str) or isinstance(visualization_output, dict),
            "Visualizer must return a text summary or structured graphical layout data"
        )
        
        if isinstance(visualization_output, str):
            self.assertIn(portfolio_id, visualization_output)
        elif isinstance(visualization_output, dict):
            self.assertEqual(visualization_output.get("portfolio_id"), portfolio_id)

if __name__ == "__main__":
    unittest.main()