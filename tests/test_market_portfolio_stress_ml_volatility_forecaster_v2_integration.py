import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import (
    forecast_portfolio_stress_volatility
)
from skills.market_portfolio_scenario_simulator import run_scenario_simulation
from skills.market_portfolio_stress_monte_carlo_engine import run_monte_carlo_stress
from skills.db_storage import save_stress_forecast_record, get_stress_forecast_record

class TestMarketPortfolioStressMlVolatilityForecasterV2Integration(unittest.TestCase):
    def test_forecast_volatility_integration_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        scenario_id = f"scen_{uuid.uuid4().hex[:8]}"
        
        base_volatility = round(random.uniform(0.1, 0.4), 4)
        stress_factor = round(random.uniform(1.5, 3.5), 2)
        confidence_level = random.choice([0.95, 0.99])
        
        simulated_scenario_data = run_scenario_simulation(
            scenario_id=scenario_id,
            base_multiplier=stress_factor
        )
        self.assertIsNotNone(simulated_scenario_data)

        mc_simulation_results = run_monte_carlo_stress(
            portfolio_id=portfolio_id,
            volatility_baseline=base_volatility,
            iterations=100
        )
        self.assertIsNotNone(mc_simulation_results)

        forecast_result = forecast_portfolio_stress_volatility(
            portfolio_id=portfolio_id,
            scenario_data=simulated_scenario_data,
            monte_carlo_metrics=mc_simulation_results,
            confidence_level=confidence_level
        )

        self.assertIsInstance(forecast_result, dict)
        self.assertEqual(forecast_result.get("portfolio_id"), portfolio_id)
        self.assertIn("predicted_volatility", forecast_result)
        self.assertGreater(forecast_result["predicted_volatility"], 0.0)

        record_id = f"rec_{uuid.uuid4().hex}"
        save_stress_forecast_record(record_id, forecast_result)

        fetched_record = get_stress_forecast_record(record_id)
        self.assertIsNotNone(fetched_record)
        self.assertEqual(fetched_record.get("portfolio_id"), portfolio_id)
        self.assertEqual(fetched_record.get("predicted_volatility"), forecast_result["predicted_volatility"])

if __name__ == "__main__":
    unittest.main()