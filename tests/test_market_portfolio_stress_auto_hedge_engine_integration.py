import unittest
import uuid
import random
import os

from skills.market_portfolio_stress_auto_hedge_engine import (
    market_portfolio_stress_auto_hedge_engine
)
from skills.market_portfolio_scenario_simulator import (
    market_portfolio_scenario_simulator
)
from skills.market_portfolio_valuation import (
    market_portfolio_valuation
)
from skills.db_storage import (
    db_storage
)

class IntegrationTestMarketPortfolioStressAutoHedgeEngine(unittest.TestCase):

    def test_auto_hedge_engine_integration_workflow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        asset_symbol = random.choice(["AAPL", "TSLA", "BTC", "ETH", "SPY"])
        position_size = round(random.uniform(1000.0, 50000.0), 2)
        stress_drop_percentage = round(random.uniform(10.0, 45.0), 2)

        valuation_input = {
            "portfolio_id": portfolio_id,
            "assets": [
                {"symbol": asset_symbol, "amount": position_size}
            ]
        }
        valuation_result = market_portfolio_valuation(valuation_input)
        self.assertIsNotNone(valuation_result)

        scenario_input = {
            "portfolio_id": portfolio_id,
            "scenario_type": "crash",
            "drop_percentage": stress_drop_percentage
        }
        simulation_result = market_portfolio_scenario_simulator(scenario_input)
        self.assertIsInstance(simulation_result, dict)

        hedge_engine_input = {
            "portfolio_id": portfolio_id,
            "simulation_data": simulation_result,
            "valuation_data": valuation_result,
            "target_mitigation_ratio": round(random.uniform(0.5, 1.0), 2)
        }
        hedge_output = market_portfolio_stress_auto_hedge_engine(hedge_engine_input)

        self.assertIsInstance(hedge_output, dict)
        self.assertIn("hedge_execution_id", hedge_output)
        
        generated_hedge_id = hedge_output["hedge_execution_id"]
        self.assertTrue(len(generated_hedge_id) > 0)

        db_check = db_storage({
            "action": "get_hedge_record",
            "hedge_execution_id": generated_hedge_id
        })
        self.assertIsNotNone(db_check)

        expected_audit_file = f"audit_hedge_{generated_hedge_id}.log"
        if os.path.exists(expected_audit_file):
            self.assertTrue(os.path.getsize(expected_audit_file) >= 0)

if __name__ == "__main__":
    unittest.main()