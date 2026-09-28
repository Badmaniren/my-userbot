import unittest
import os
import uuid
import random
import string
import json

from skills.market_portfolio_rebalance_planner import MarketPortfolioRebalancePlanner

class TestMarketPortfolioRebalancePlannerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = f"/tmp/test_planner_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)
        self.storage_path = os.path.join(self.test_dir, f"db_{uuid.uuid4().hex}.json")
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=4))

        # Seed json file so symbol exists for scenario simulation
        data = {
            self.symbol: {"current_price": 100.0, "quantity": 10}
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f)

        self.planner = MarketPortfolioRebalancePlanner(self.storage_path)

    def tearDown(self):
        if os.path.exists(self.storage_path):
            try:
                os.remove(self.storage_path)
            except OSError:
                pass
        if os.path.exists(self.test_dir):
            try:
                os.rmdir(self.test_dir)
            except OSError:
                pass

    def test_plan_and_execute_integration(self):
        shifts = random.randint(1, 10)
        percentage = round(random.uniform(0.01, 0.5), 2)

        result = self.planner.plan_and_execute(self.symbol, shifts, percentage)
        self.assertIsInstance(result, dict)
        self.assertIn("execution_id", result)
        self.assertIn("status", result)

    def test_run_batch_rebalance_integration(self):
        symbols = [''.join(random.choices(string.ascii_uppercase, k=3)) for _ in range(3)]
        data = {}
        for sym in symbols:
            data[sym] = {"current_price": 100.0, "quantity": 10}

        with open(self.storage_path, 'w') as f:
            json.dump(data, f)

        percentage = round(random.uniform(0.05, 0.25), 2)

        results = self.planner.run_batch_rebalance(symbols, percentage)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), len(symbols))

    def test_get_rebalance_readiness_integration(self):
        readiness = self.planner.get_rebalance_readiness(self.symbol)
        self.assertIsInstance(readiness, dict)
        self.assertIn(self.symbol, readiness)
        self.assertEqual(readiness[self.symbol]["summary"], "active")

    def test_verify_stress_resilience_integration(self):
        ticker = ''.join(random.choices(string.ascii_uppercase, k=4))
        shifts = [round(random.uniform(-0.1, 0.1), 2) for _ in range(3)]
        volume = random.randint(100, 500)
        scenario = f"scenario_{uuid.uuid4().hex[:6]}"

        report = self.planner.verify_stress_resilience(ticker, shifts, volume, scenario)
        self.assertIsInstance(report, dict)
        self.assertIn("stress_scenario", report)
        self.assertIn("stress_slippage", report)

if __name__ == '__main__':
    unittest.main()
