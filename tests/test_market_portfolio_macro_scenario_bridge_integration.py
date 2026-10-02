import unittest
import uuid
import random
import os
from skills.market_portfolio_macro_scenario_bridge import market_portfolio_macro_scenario_bridge, MarketPortfolioMacroScenarioBridgeException
from skills.db_storage import db_storage

class TestMarketPortfolioMacroScenarioBridgeIntegration(unittest.TestCase):
    def test_execute_multi_factor_forecast_integration(self):
        portfolio_id = f"port_{uuid.uuid4()}"
        scenario_id = f"scen_{uuid.uuid4()}"
        macro_factor_id = f"macro_{uuid.uuid4()}"
        output_destination = f"test_output_{uuid.uuid4()}.txt"

        gdp_shock_val = round(random.uniform(-10.0, 10.0), 2)

        db_storage.save_macro_scenario_forecast({
            "macro_factor_id": macro_factor_id,
            "applied_gdp_shock": gdp_shock_val
        })

        payload = {
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "macro_factor_id": macro_factor_id,
            "output_destination": output_destination
        }

        try:
            result = market_portfolio_macro_scenario_bridge.execute_multi_factor_forecast(payload)

            self.assertEqual(result["portfolio_id"], portfolio_id)
            self.assertEqual(result["scenario_id"], scenario_id)
            self.assertEqual(result["macro_factor_id"], macro_factor_id)
            self.assertEqual(result["applied_gdp_shock"], gdp_shock_val)
            self.assertIn("forecast_id", result)

            self.assertTrue(os.path.exists(output_destination))
            with open(output_destination, "r") as f:
                content = f.read()
            self.assertIn(result["forecast_id"], content)
        finally:
            if os.path.exists(output_destination):
                os.remove(output_destination)

    def test_execute_multi_factor_forecast_missing_params(self):
        payload = {
            "portfolio_id": f"port_{uuid.uuid4()}"
        }
        with self.assertRaises(MarketPortfolioMacroScenarioBridgeException):
            market_portfolio_macro_scenario_bridge.execute_multi_factor_forecast(payload)

    def test_execute_multi_factor_forecast_not_found(self):
        payload = {
            "portfolio_id": f"port_{uuid.uuid4()}",
            "scenario_id": f"scen_{uuid.uuid4()}",
            "macro_factor_id": f"nonexistent_{uuid.uuid4()}"
        }
        with self.assertRaises(MarketPortfolioMacroScenarioBridgeException):
            market_portfolio_macro_scenario_bridge.execute_multi_factor_forecast(payload)

if __name__ == "__main__":
    unittest.main()