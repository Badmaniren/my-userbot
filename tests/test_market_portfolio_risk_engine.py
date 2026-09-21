import unittest
import unittest.mock
import random
import uuid
import io
import os
from skills.market_portfolio_risk_engine import RiskEngine

class TestMarketPortfolioRiskEngine(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.engine = RiskEngine(self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_calculate_volatility_logic(self):
        symbol = uuid.uuid4().hex
        random_prices = [random.uniform(10.0, 500.0) for _ in range(10)]

        with unittest.mock.patch('skills.market_portfolio_risk_engine.RiskEngine.load_data') as mock_load:
            mock_load.return_value = random_prices

            result = self.engine.calculate_volatility(symbol)

            self.assertIsInstance(result, float)
            self.assertGreaterEqual(result, 0.0)
            mock_load.assert_called_once_with(self.storage_file)

    def test_calculate_var_with_random_confidence(self):
        symbol = uuid.uuid4().hex
        confidence = random.choice([0.95, 0.99])
        random_returns = [random.uniform(-0.05, 0.05) for _ in range(100)]

        with unittest.mock.patch('skills.market_portfolio_risk_engine.RiskEngine.load_data') as mock_load:
            mock_load.return_value = random_returns

            var_value = self.engine.calculate_var(symbol, confidence)

            self.assertIsInstance(var_value, float)
            self.assertLess(var_value, 0.0)

    def test_risk_engine_data_integrity(self):
        symbol = uuid.uuid4().hex
        random_data = {symbol: [random.uniform(1, 100) for _ in range(5)]}

        with unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data=str(random_data))):
            with unittest.mock.patch('os.path.exists', return_value=True):
                data = self.engine.load_data(self.storage_file)
                self.assertEqual(data, random_data[symbol])

    def test_empty_data_handling(self):
        symbol = uuid.uuid4().hex

        with unittest.mock.patch('skills.market_portfolio_risk_engine.RiskEngine.load_data') as mock_load:
            mock_load.return_value = []

            with self.assertRaises(ValueError):
                self.engine.calculate_volatility(symbol)

    def test_var_calculation_precision(self):
        symbol = uuid.uuid4().hex
        # Фиксированный набор для проверки математической корректности
        fixed_returns = [-0.1, -0.05, -0.02, 0.01, 0.02]

        with unittest.mock.patch('skills.market_portfolio_risk_engine.RiskEngine.load_data') as mock_load:
            mock_load.return_value = fixed_returns

            result = self.engine.calculate_var(symbol, 0.95)

            # Проверка, что VaR находится в рамках диапазона доходностей
            self.assertIn(result, fixed_returns)

if __name__ == '__main__':
    unittest.main()