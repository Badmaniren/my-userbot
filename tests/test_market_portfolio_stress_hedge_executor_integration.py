import unittest
import uuid
import random
import os
from datetime import datetime

from skills.market_portfolio_stress_hedge_executor import (
    market_portfolio_stress_hedge_executor
)
from skills.market_portfolio_stress_monte_carlo_engine import (
    market_portfolio_stress_monte_carlo_engine
)
from skills.market_portfolio_scenario_simulator import (
    market_portfolio_scenario_simulator
)
from skills.market_portfolio_execution_pipeline import (
    market_portfolio_execution_pipeline
)
from skills.db_storage import db_storage

class IntegrationTestMarketPortfolioStressHedgeExecutor(unittest.TestCase):

    def test_stress_hedge_executor_real_pipeline(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        asset_symbol = random.choice(["BTC-USD", "ETH-USD", "SPY", "QQQ", "GLD"])
        initial_value = round(random.uniform(50000.0, 500000.0), 2)
        confidence_level = random.choice([0.95, 0.99])
        simulations_count = random.randint(100, 1000)

        market_data = {
            "portfolio_id": portfolio_id,
            "asset_symbol": asset_symbol,
            "initial_value": initial_value,
            "timestamp": datetime.utcnow().isoformat()
        }

        sim_result = market_portfolio_scenario_simulator(market_data)
        self.assertIsNotNone(sim_result, "Scenario simulator must return evaluation data")

        mc_input = {
            "portfolio_id": portfolio_id,
            "scenario_data": sim_result,
            "confidence_level": confidence_level,
            "simulations_count": simulations_count
        }

        mc_result = market_portfolio_stress_monte_carlo_engine(mc_input)
        self.assertIsInstance(mc_result, dict, "Monte Carlo engine must return dictionary results")
        self.assertIn("var_value", mc_result)

        executor_payload = {
            "portfolio_id": portfolio_id,
            "monte_carlo_report": mc_result,
            "execution_mode": "live_hedging",
            "risk_tolerance_threshold": random.uniform(0.01, 0.05)
        }

        hedge_execution_result = market_portfolio_stress_hedge_executor(executor_payload)

        self.assertIsInstance(hedge_execution_result, dict)
        self.assertIn("execution_id", hedge_execution_result)

        exec_id = hedge_execution_result["execution_id"]
        self.assertTrue(len(exec_id) > 0, "Execution ID must not be empty")

        pipeline_check = market_portfolio_execution_pipeline({
            "execution_id": exec_id,
            "portfolio_id": portfolio_id
        })
        self.assertIsNotNone(pipeline_check)

        stored_record = db_storage({
            "action": "get",
            "table": "hedge_executions",
            "id": exec_id
        })
        self.assertIsNotNone(stored_record, "Hedge execution must be persisted in db_storage")
        self.assertEqual(stored_record.get("portfolio_id"), portfolio_id)

if __name__ == "__main__":
    unittest.main()