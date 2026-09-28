import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import string

from skills.market_portfolio_rebalance_executor import RebalanceExecutor
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer
from skills.market_portfolio_api_gateway import MarketPortfolioAPIGateway

class TestRebalanceExecutor(unittest.TestCase):

    def setUp(self):
        self.storage_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.executor = RebalanceExecutor(storage_file=self.storage_path)

    def test_execute_rebalance_flow(self):
        # Генерируем случайные параметры
        symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        shifts = random.randint(1, 100)
        percentage = random.uniform(0.01, 0.99)
        url = f"https://{uuid.uuid4().hex}.com/api"

        # Ожидаемый результат от стратегии
        expected_strategy = {"action": "buy", "target": symbol, "weight": percentage}

        with patch('skills.market_portfolio_strategy_optimizer.PortfolioStrategyOptimizer.optimize_strategy') as mock_opt:
            with patch('skills.market_portfolio_api_gateway.MarketPortfolioAPIGateway.export_portfolio_summary') as mock_gateway:

                mock_opt.return_value = expected_strategy
                mock_gateway.return_value = {"status": "success", "tx_id": uuid.uuid4().hex}

                # Выполнение
                result = self.executor.execute_rebalance(symbol, shifts, percentage, url)

                # Проверка вызовов
                mock_opt.assert_called_once_with(symbol, shifts, percentage)
                self.assertEqual(result['strategy'], expected_strategy)
                self.assertIn('tx_id', result['gateway_response'])

    def test_rebalance_failure_handling(self):
        # Генерируем случайные данные для теста ошибки
        symbol = uuid.uuid4().hex[:5]
        shifts = random.randint(10, 50)
        percentage = random.random()
        url = f"http://{uuid.uuid4().hex}.io"

        with patch('skills.market_portfolio_strategy_optimizer.PortfolioStrategyOptimizer.optimize_strategy') as mock_opt:
            # Имитируем исключение в стратегии
            mock_opt.side_effect = Exception("Strategy calculation failed")

            with self.assertRaises(Exception) as context:
                self.executor.execute_rebalance(symbol, shifts, percentage, url)

            self.assertTrue("Strategy calculation failed" in str(context.exception))

    def test_integration_with_gateway_data(self):
        # Проверка передачи данных в шлюз
        symbol = uuid.uuid4().hex
        url = f"https://api.{uuid.uuid4().hex}.net"

        with patch('skills.market_portfolio_api_gateway.MarketPortfolioAPIGateway.export_portfolio_summary') as mock_gateway:
            # Генерируем случайный ответ от шлюза
            random_response = {"data": uuid.uuid4().hex, "code": random.randint(200, 500)}
            mock_gateway.return_value = random_response

            # Вызываем метод, который должен использовать шлюз
            response = self.executor.sync_portfolio_state(url)

            self.assertEqual(response, random_response)
            mock_gateway.assert_called_with(url)

    def test_strategy_resilience_check(self):
        # Проверка вызова метода оценки устойчивости
        symbol = uuid.uuid4().hex
        shifts = random.randint(1, 10)

        with patch('skills.market_portfolio_strategy_optimizer.PortfolioStrategyOptimizer.evaluate_resilience') as mock_resilience:
            expected_resilience = {"score": random.random(), "id": uuid.uuid4().hex}
            mock_resilience.return_value = expected_resilience

            result = self.executor.check_strategy_health(symbol, shifts)

            self.assertEqual(result, expected_resilience)
            mock_resilience.assert_called_once_with(symbol, shifts)

if __name__ == '__main__':
    unittest.main()