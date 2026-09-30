import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_resilience_analyzer import market_portfolio_stress_resilience_analyzer
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_stress_reporter import market_portfolio_stress_reporter

class TestMarketPortfolioStressResilienceIntegration(unittest.TestCase):
    def test_stress_resilience_analyzer_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        asset_symbol = random.choice(["BTC", "ETH", "SPY", "QQQ", "GLD"])
        initial_amount = round(random.uniform(10000.0, 1000000.0), 2)
        shock_percentage = round(random.uniform(-50.0, -10.0), 2)

        collector_payload = {
            "portfolio_id": portfolio_id,
            "asset": asset_symbol,
            "amount": initial_amount,
            "historical_mode": True
        }
        collected_data = market_portfolio_collector_agent(collector_payload)
        self.assertIn("data_collected", collected_data)

        simulator_payload = {
            "portfolio_id": portfolio_id,
            "market_data": collected_data,
            "shock_percentage": shock_percentage
        }
        simulation_result = market_portfolio_scenario_simulator(simulator_payload)
        self.assertIn("simulated_portfolio_value", simulation_result)

        db_payload = {
            "record_id": uuid.uuid4().hex,
            "portfolio_id": portfolio_id,
            "simulation_result": simulation_result
        }
        db_storage_response = db_storage(db_payload)
        self.assertTrue(db_storage_response.get("success", False))

        analyzer_payload = {
            "portfolio_id": portfolio_id,
            "db_reference": db_payload["record_id"],
            "threshold": shock_percentage
        }
        analysis_result = market_portfolio_stress_resilience_analyzer(analyzer_payload)
        self.assertEqual(analysis_result.get("portfolio_id"), portfolio_id)
        self.assertIn("resilience_score", analysis_result)

        reporter_payload = {
            "portfolio_id": portfolio_id,
            "analysis": analysis_result,
            "output_format": "json"
        }
        report_output = market_portfolio_stress_reporter(reporter_payload)
        
        report_file_path = report_output.get("file_path")
        if report_file_path:
            self.assertTrue(os.path.exists(report_file_path))
            if os.path.exists(report_file_path):
                os.remove(report_file_path)

if __name__ == "__main__":
    unittest.main()