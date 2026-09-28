import unittest
import uuid
import random
import os

from skills.market_portfolio_stress_monte_carlo import run_monte_carlo_stress_test
from skills.db_storage import save_stress_result, get_stress_result
from skills.market_portfolio_slippage_model import calculate_slippage
from skills.market_anomaly_detector import detect_anomalies

class IntegrationTestMarketPortfolioStressMonteCarlo(unittest.TestCase):
    def test_monte_carlo_stress_integration(self):
        portfolio_id = str(uuid.uuid4())
        initial_capital = round(random.uniform(10000.0, 1000000.0), 2)
        iterations = random.randint(100, 1000)
        volatility = round(random.uniform(0.1, 0.5), 4)

        anomalies = detect_anomalies(portfolio_id=portfolio_id)
        self.assertIsInstance(anomalies, list)

        slippage_data = calculate_slippage(portfolio_id=portfolio_id, volume=initial_capital)
        self.assertIn("slippage_rate", slippage_data)

        stress_output = run_monte_carlo_stress_test(
            portfolio_id=portfolio_id,
            capital=initial_capital,
            iterations=iterations,
            volatility=volatility,
            anomalies=anomalies,
            slippage=slippage_data["slippage_rate"]
        )

        self.assertIn("simulation_id", stress_output)
        self.assertEqual(stress_output["portfolio_id"], portfolio_id)
        self.assertIn("var_95", stress_output)

        sim_id = stress_output["simulation_id"]
        save_stress_result(simulation_id=sim_id, data=stress_output)

        retrieved_data = get_stress_result(simulation_id=sim_id)
        self.assertIsNotNone(retrieved_data)
        self.assertEqual(retrieved_data["simulation_id"], sim_id)
        self.assertEqual(retrieved_data["portfolio_id"], portfolio_id)
        self.assertEqual(retrieved_data["initial_capital"], initial_capital)

        report_path = f"reports/stress_{sim_id}.json"
        self.assertTrue(os.path.exists(report_path) or "report_path" in stress_output)
        if "report_path" in stress_output:
            self.assertTrue(os.path.exists(stress_output["report_path"]))

if __name__ == "__main__":
    unittest.main()