import unittest
import os
import uuid
import random
import json
from skills.market_portfolio_strategy_optimizer import PortfolioStrategyOptimizer
from skills.market_portfolio_api_gateway import MarketPortfolioAPIGateway
from skills.market_portfolio_rebalance_executor import RebalanceExecutor

class TestMarketPortfolioRebalanceExecutorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())
        self.storage_file = f"test_storage_{self.test_id}.json"
        self.symbol = f"TICKER_{random.randint(1000, 9999)}"
        self.shifts = random.randint(1, 10)
        self.percentage = random.uniform(0.01, 0.20)

        # Инициализация реальных компонентов
        self.optimizer = PortfolioStrategyOptimizer(self.storage_file)
        self.gateway = MarketPortfolioAPIGateway(self.storage_file)
        self.executor = RebalanceExecutor(self.optimizer, self.gateway)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            os.remove(self.storage_file)

    def test_rebalance_execution_flow(self):
        # 1. Генерация стратегии через оптимизатор
        strategy_result = self.optimizer.optimize_strategy(
            self.symbol,
            self.shifts,
            self.percentage
        )
        self.assertIn("status", strategy_result)

        # 2. Исполнение ребалансировки через executor
        # Передаем данные, полученные из реального модуля стратегии
        execution_result = self.executor.execute_rebalance(
            symbol=self.symbol,
            strategy_data=strategy_result,
            transaction_id=self.test_id
        )

        # Проверка: исполнитель должен вернуть подтверждение транзакции
        self.assertEqual(execution_result.get("transaction_id"), self.test_id)
        self.assertTrue(execution_result.get("success"))

        # 3. Проверка интеграции с API Gateway (экспорт состояния)
        # Проверяем, что данные попали в хранилище и доступны через шлюз
        summary = self.gateway.export_portfolio_summary(url="http://localhost:8080")

        # Проверка того, что файл хранилища был обновлен реальными данными
        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, 'r') as f:
            data = json.load(f)
            self.assertIn(self.symbol, str(data))

    def test_resilience_evaluation_integration(self):
        # Проверка связки оценки устойчивости и исполнения
        resilience = self.optimizer.evaluate_resilience(self.symbol, self.shifts)

        # Если устойчивость выше порога, исполняем
        if resilience.get("score", 0) > 0.5:
            result = self.executor.execute_rebalance(
                self.symbol,
                {"action": "BUY", "amount": random.randint(1, 100)},
                self.test_id
            )
            self.assertIsNotNone(result)
            self.assertEqual(result.get("symbol"), self.symbol)

if __name__ == '__main__':
    unittest.main()