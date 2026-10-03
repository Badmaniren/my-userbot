import unittest
import uuid
import random
import os
from skills.market_portfolio_macro_liquidity_bridge import (
    db_storage,
    extractor_tool_1790087207,
    market_portfolio_liquidity_scenario_analyzer,
    market_portfolio_stress_monte_carlo_engine,
    market_portfolio_audit_compliance_hub
)

class TestMarketPortfolioMacroLiquidityBridgeIntegration(unittest.TestCase):
    def test_macro_liquidity_bridge_end_to_end(self):
        run_id = str(uuid.uuid4())
        liquidity_factor = random.uniform(0.1, 0.9)
        portfolio_id = f"portfolio_{uuid.uuid4().hex[:8]}"

        storage = db_storage()
        self.assertIsNotNone(storage)

        raw_data = extractor_tool_1790087207(run_id=run_id, factor=liquidity_factor)
        self.assertIsNotNone(raw_data)

        scenario_analyzer = market_portfolio_liquidity_scenario_analyzer()
        scenario_result = scenario_analyzer.analyze(portfolio_id=portfolio_id, liquidity_data=raw_data)
        self.assertIn("status", scenario_result)

        mc_engine = market_portfolio_stress_monte_carlo_engine()
        stress_simulation = mc_engine.simulate(portfolio_id=portfolio_id, scenario=scenario_result)
        self.assertIsNotNone(stress_simulation)

        compliance_hub = market_portfolio_audit_compliance_hub()
        audit_record = compliance_hub.verify_and_log(run_id=run_id, simulation_result=stress_simulation)

        output_file_path = f"audit_report_{run_id}.log"
        self.assertTrue(os.path.exists(output_file_path) or audit_record is not None)

        if os.path.exists(output_file_path):
            with open(output_file_path, "r") as f:
                content = f.read()
                self.assertIn(run_id, content)
            os.remove(output_file_path)

if __name__ == "__main__":
    unittest.main()