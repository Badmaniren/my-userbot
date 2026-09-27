import unittest
import os
import uuid
import random
from skills.market_portfolio_simulation_evaluator import evaluate_portfolio_simulation

class TestMarketPortfolioSimulationEvaluatorIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_portfolio_storage_{uuid.uuid4()}.json"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"

        # Создаем базовый файл с данными, необходимыми для работы аналитики и симулятора
        initial_data = f'{{"symbol": "{self.symbol}", "price": {random.uniform(10.0, 500.0):.2f}, "history": [100, 105, 102, 110]}}'
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write(initial_data)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_simulation_evaluator_integration(self):
        percentage = round(random.uniform(-0.2, 0.2), 4)

        result = evaluate_portfolio_simulation(self.storage_file, self.symbol, percentage)

        self.assertIsInstance(result, dict)
        self.assertTrue(len(result) > 0)
        self.assertIn("simulation", result)
        self.assertIn("analytics", result)

if __name__ == "__main__":
    unittest.main()