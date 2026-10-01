import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_backtest_sync import (
    market_portfolio_stress_backtest_sync,
    market_portfolio_scenario_simulator,
    market_portfolio_backtester,
    db_storage
)

class TestMarketPortfolioStressBacktestSyncIntegration(unittest.TestCase):
    def test_sync_stress_and_backtest_predictive_power(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        scenario_id = f"scen_{uuid.uuid4().hex[:8]}"
        initial_capital = round(random.uniform(10000.0, 1000000.0), 2)
        stress_shock_pct = round(random.uniform(-0.5, -0.05), 4)

        simulator_input = {
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "shock_percentage": stress_shock_pct,
            "capital": initial_capital
        }

        simulated_stress_result = market_portfolio_scenario_simulator(simulator_input)
        self.assertIsNotNone(simulated_stress_result)

        backtest_input = {
            "portfolio_id": portfolio_id,
            "historical_window_days": random.randint(30, 365),
            "initial_capital": initial_capital
        }

        historical_backtest_result = market_portfolio_backtester(backtest_input)
        self.assertIsNotNone(historical_backtest_result)

        sync_payload = {
            "sync_id": f"sync_{uuid.uuid4().hex}",
            "portfolio_id": portfolio_id,
            "scenario_result": simulated_stress_result,
            "backtest_result": historical_backtest_result,
            "evaluation_metric": "predictive_power_divergence"
        }

        sync_execution_output = market_portfolio_stress_backtest_sync(sync_payload)

        self.assertIsInstance(sync_execution_output, dict)
        self.assertIn("sync_id", sync_execution_output)
        self.assertEqual(sync_execution_output["sync_id"], sync_payload["sync_id"])
        self.assertIn("predictive_score", sync_execution_output)

        stored_record = db_storage.get(f"sync_record_{sync_payload['sync_id']}")
        self.assertIsNotNone(stored_record)
        self.assertEqual(stored_record["portfolio_id"], portfolio_id)

if __name__ == "__main__":
    unittest.main()