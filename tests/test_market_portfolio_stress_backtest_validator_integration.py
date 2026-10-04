import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_backtest_validator import (
    market_portfolio_stress_backtest_validator,
)
from skills.market_portfolio_stress_scenario_pipeline import (
    market_portfolio_stress_scenario_pipeline,
)
from skills.market_portfolio_backtester import market_portfolio_backtester
from skills.db_storage import db_storage


class TestMarketPortfolioStressBacktestValidatorIntegration(unittest.TestCase):

    def test_stress_backtest_validation_pipeline_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        initial_capital = round(random.uniform(10000.0, 1000000.0), 2)
        scenario_id = f"scen_{uuid.uuid4().hex[:8]}"

        scenario_data = {
            "scenario_id": scenario_id,
            "portfolio_id": portfolio_id,
            "shock_percentage": round(random.uniform(-0.5, -0.1), 2),
            "historical_window_days": random.randint(30, 365)
        }

        pipeline_result = market_portfolio_stress_scenario_pipeline(scenario_data)
        self.assertIsNotNone(pipeline_result)

        backtest_config = {
            "portfolio_id": portfolio_id,
            "initial_capital": initial_capital,
            "strategy": "stress_validation_run"
        }
        backtest_result = market_portfolio_backtester(backtest_config)
        self.assertIsNotNone(backtest_result)

        validation_payload = {
            "validation_run_id": f"val_{uuid.uuid4().hex}",
            "portfolio_id": portfolio_id,
            "scenario_result": pipeline_result,
            "backtest_result": backtest_result,
            "tolerance_threshold": round(random.uniform(0.01, 0.15), 4)
        }

        validator_output = market_portfolio_stress_backtest_validator(validation_payload)

        self.assertIsInstance(validator_output, dict)
        self.assertIn("validation_status", validator_output)
        self.assertIn("accuracy_score", validator_output)

        stored_record = db_storage(
            action="get",
            key=validation_payload["validation_run_id"]
        )
        self.assertIsNotNone(stored_record)


if __name__ == "__main__":
    unittest.main()