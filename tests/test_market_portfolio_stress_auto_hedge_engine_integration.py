import unittest
import uuid
import os
import random
from skills import market_portfolio_stress_auto_hedge_engine
from skills import db_storage

class TestMarketPortfolioStressAutoHedgeIntegration(unittest.TestCase):
    def test_run_stress_auto_hedge_engine_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        scenario_data = {"drop_percent": round(random.uniform(5.0, 25.0), 2)}
        monte_carlo_data = {"var_95": round(random.uniform(1000.0, 50000.0), 2)}
        capital = round(random.uniform(100000.0, 1000000.0), 2)

        result = market_portfolio_stress_auto_hedge_engine.run_stress_auto_hedge_engine(
            portfolio_id=portfolio_id,
            scenario_data=scenario_data,
            monte_carlo_data=monte_carlo_data,
            capital=capital
        )

        self.assertIn("hedge_orders", result)
        self.assertIn("report_file_path", result)

        hedge_orders = result["hedge_orders"]
        self.assertGreater(len(hedge_orders), 0)

        order = hedge_orders[0]
        self.assertEqual(order["portfolio_id"], portfolio_id)
        self.assertEqual(order["type"], "PUT_OPTION")
        self.assertAlmostEqual(order["capital_allocated"], capital * 0.05)

        report_path = result["report_file_path"]
        self.assertTrue(os.path.exists(report_path))

        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(portfolio_id, content)
            self.assertIn(str(scenario_data), content)
            self.assertIn(str(monte_carlo_data), content)

        if os.path.exists(report_path):
            os.remove(report_path)

if __name__ == "__main__":
    unittest.main()