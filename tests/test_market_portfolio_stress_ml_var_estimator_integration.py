import unittest
import uuid
import random
import os

from skills.market_portfolio_stress_ml_var_estimator import (
    market_portfolio_stress_ml_var_estimator
)
from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import (
    market_portfolio_stress_ml_volatility_forecaster_v2
)
from skills.market_portfolio_stress_monte_carlo_engine import (
    market_portfolio_stress_monte_carlo_engine
)
from skills.market_portfolio_var_liquidity_core import (
    market_portfolio_var_liquidity_core
)
from skills.db_storage import db_storage

class TestMarketPortfolioStressMlVarEstimatorIntegration(unittest.TestCase):
    def test_var_estimator_integration_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        simulation_runs = random.randint(100, 1000)
        confidence_level = round(random.uniform(0.95, 0.99), 4)

        volatility_forecast = market_portfolio_stress_ml_volatility_forecaster_v2(
            portfolio_id=portfolio_id,
            horizon_days=random.choice([5, 10, 30])
        )

        self.assertIsInstance(volatility_forecast, dict)

        monte_carlo_results = market_portfolio_stress_monte_carlo_engine(
            portfolio_id=portfolio_id,
            runs=simulation_runs,
            vol_data=volatility_forecast
        )

        self.assertIsInstance(monte_carlo_results, dict)

        liquidity_metrics = market_portfolio_var_liquidity_core(
            portfolio_id=portfolio_id,
            simulation_data=monte_carlo_results
        )

        self.assertIsInstance(liquidity_metrics, dict)

        var_estimation = market_portfolio_stress_ml_var_estimator(
            portfolio_id=portfolio_id,
            confidence=confidence_level,
            vol_forecaster_output=volatility_forecast,
            monte_carlo_output=monte_carlo_results,
            liquidity_core_output=liquidity_metrics
        )

        self.assertIsInstance(var_estimation, dict)
        self.assertIn("var_value", var_estimation)

        db_save_status = db_storage(
            record_id=portfolio_id,
            data=var_estimation
        )

        self.assertTrue(db_save_status)

if __name__ == "__main__":
    unittest.main()