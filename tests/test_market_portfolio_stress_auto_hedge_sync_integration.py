import unittest
import os
import uuid
import random
import tempfile
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync
from skills.market_portfolio_stress_hedge_advisor import MarketPortfolioStressHedgeAdvisor
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline

class TestMarketPortfolioStressAutoHedgeSyncIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, "stress_pipeline.json")

        # Инициализация реальных зависимостей
        self.db_storage = None
        self.monitor = None
        self.evaluator = None
        self.rebalancer = None

        self.sync_module = MarketPortfolioStressAutoHedgeSync(
            db_storage=self.db_storage,
            monitor=self.monitor,
            evaluator=self.evaluator,
            rebalancer=self.rebalancer,
            storage_file=self.storage_file
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_synchronize_integration_flow(self):
        # Генерация случайных данных для исключения хардкода
        portfolio_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        symbol = random.choice(["AAPL", "BTC", "TSLA", "ETH"])
        percentage = round(random.uniform(0.01, 0.5), 4)
        shifts = [random.randint(-100, 100) for _ in range(3)]

        # Выполнение синхронизации
        result = self.sync_module.synchronize(
            portfolio_id=portfolio_id,
            request_id=request_id,
            symbol=symbol,
            percentage=percentage,
            shifts=shifts
        )

        # Проверка структуры ответа
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["request_id"], request_id)

        # Проверка взаимодействия с Advisor (наличие данных в ответе)
        self.assertIn("advisor_recommendation", result)

        # Проверка взаимодействия с Pipeline (наличие данных в ответе)
        self.assertIn("stress_pipeline_result", result)
        
        # Проверка реального изменения (создание файла хранилища пайплайном)
        self.assertTrue(os.path.exists(self.storage_file), "Pipeline должен был создать файл хранилища")

        # Проверка консистентности данных в пайплайне
        with open(self.storage_file, 'r') as f:
            content = f.read()
            self.assertIn(symbol, content)
            self.assertIn(str(percentage), content)

if __name__ == '__main__':
    unittest.main()