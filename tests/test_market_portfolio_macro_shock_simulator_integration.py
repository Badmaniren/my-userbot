import unittest
import uuid
import random
from skills.market_portfolio_macro_shock_simulator import market_portfolio_macro_shock_simulator

class TestMarketPortfolioMacroShockSimulatorIntegration(unittest.TestCase):
    def test_macro_shock_simulator_integration(self):
        rand_suffix = uuid.uuid4().hex[:6]
        portfolio_id = f"port_{rand_suffix}"
        scenario_id = f"scen_{rand_suffix}"
        shock_id = f"shock_{rand_suffix}"

        current_price = round(random.uniform(50.0, 500.0), 2)
        volume = random.randint(10, 1000)
        inflation_shock = round(random.uniform(0.01, 0.15), 4)
        rate_hike = random.randint(10, 100)

        payload = {
            "shock_id": shock_id,
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id,
            "assets": [
                {
                    "asset_id": f"asset_{uuid.uuid4().hex[:4]}",
                    "ticker": f"TICK_{rand_suffix}",
                    "current_price": current_price,
                    "volume": volume
                }
            ],
            "macro_variables": {
                "inflation_shock": inflation_shock,
                "central_bank_rate_hike": rate_hike
            }
        }

        result = market_portfolio_macro_shock_simulator(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("shock_id"), shock_id)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("scenario_id"), scenario_id)

        impact_results = result.get("impact_results")
        self.assertIsInstance(impact_results, list)
        self.assertTrue(len(impact_results) > 0)

        asset_impact = impact_results[0]
        expected_valuation = (current_price * volume) * (1.0 - (inflation_shock + (rate_hike / 1000.0)))

        self.assertAlmostEqual(asset_impact.get("adjusted_valuation"), expected_valuation, places=4)

if __name__ == "__main__":
    unittest.main()