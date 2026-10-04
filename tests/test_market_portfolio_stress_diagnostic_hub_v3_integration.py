import unittest
import uuid
import random
from skills.market_portfolio_stress_diagnostic_hub_v3 import market_portfolio_stress_diagnostic_hub_v3_execute
from skills.db_storage import db_storage_client

class TestMarketPortfolioStressDiagnosticHubV3Integration(unittest.TestCase):
    def test_diagnostic_hub_integration_real_flow(self):
        rand_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        rand_capital = round(random.uniform(10000.0, 1000000.0), 2)
        rand_shock = round(random.uniform(-50.0, -5.0), 2)
        rand_sim_val = random.randint(100, 500)
        rand_mc_val = random.randint(1000, 5000)

        payload = {
            "portfolio_id": rand_portfolio_id,
            "initial_capital": rand_capital,
            "shock_pct": rand_shock,
            "sim_data": rand_sim_val,
            "mc_data": rand_mc_val
        }

        result = market_portfolio_stress_diagnostic_hub_v3_execute(payload)

        self.assertIsInstance(result, dict)
        self.assertIn("diagnostic_id", result)
        diag_id = result["diagnostic_id"]
        self.assertEqual(result["portfolio_id"], rand_portfolio_id)
        self.assertEqual(result["initial_capital"], rand_capital)
        self.assertEqual(result["shock_pct"], rand_shock)
        self.assertEqual(result["sim_data"], rand_sim_val)
        self.assertEqual(result["mc_data"], rand_mc_val)
        self.assertEqual(result["status"], "SUCCESS")

        stored_record = db_storage_client.get(f"stress_diag_{diag_id}")
        self.assertIsNotNone(stored_record)
        self.assertEqual(stored_record.get("diagnostic_id"), diag_id)
        self.assertEqual(stored_record.get("portfolio_id"), rand_portfolio_id)
        self.assertEqual(stored_record.get("initial_capital"), rand_capital)

if __name__ == "__main__":
    unittest.main()