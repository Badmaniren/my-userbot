import unittest
import uuid
import random
import os

from skills.market_portfolio_stress_backtest_reporting_hub import market_portfolio_stress_backtest_reporting_hub
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_backtester import market_portfolio_backtester
from skills.db_storage import db_storage

class TestMarketPortfolioStressBacktestReportingHubIntegration(unittest.TestCase):

    def test_stress_backtest_reporting_hub_end_to_end(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_capital = round(random.uniform(50000.0, 500000.0), 2)
        stress_factor = round(random.uniform(0.1, 0.5), 2)

        simulation_result = market_portfolio_scenario_simulator(
            portfolio_id=portfolio_id,
            stress_factor=stress_factor
        )
        self.assertIsNotNone(simulation_result)

        backtest_result = market_portfolio_backtester(
            portfolio_id=portfolio_id,
            capital=initial_capital,
            scenario_data=simulation_result
        )
        self.assertIsNotNone(backtest_result)

        report_id = f"rep_{uuid.uuid4().hex}"
        hub_output = market_portfolio_stress_backtest_reporting_hub(
            report_id=report_id,
            portfolio_id=portfolio_id,
            backtest_data=backtest_result
        )

        self.assertIsInstance(hub_output, dict)
        self.assertEqual(hub_output.get("report_id"), report_id)
        self.assertEqual(hub_output.get("portfolio_id"), portfolio_id)
        self.assertIn("resilience_metrics", hub_output)

        stored_record = db_storage(action="get", key=report_id)
        self.assertIsNotNone(stored_record)
        self.assertEqual(stored_record.get("report_id"), report_id)

if __name__ == "__main__":
    unittest.main()