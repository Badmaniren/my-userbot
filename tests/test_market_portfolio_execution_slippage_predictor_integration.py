import unittest
import uuid
import random
import os
from skills.market_portfolio_execution_slippage_predictor import MarketPortfolioExecutionSlippagePredictor
from skills.market_portfolio_liquidity_scenario_analyzer import MarketPortfolioLiquidityScenarioAnalyzer
from skills.market_portfolio_slippage_model import MarketPortfolioSlippageModel
from skills.db_storage import DBStorage

class TestMarketPortfolioExecutionSlippagePredictorIntegration(unittest.TestCase):
    def setUp(self):
        self.db = DBStorage()
        self.liquidity_analyzer = MarketPortfolioLiquidityScenarioAnalyzer()
        self.slippage_model = MarketPortfolioSlippageModel()
        self.predictor = MarketPortfolioExecutionSlippagePredictor(
            db_storage=self.db,
            liquidity_analyzer=self.liquidity_analyzer,
            slippage_model=self.slippage_model
        )
        self.test_run_id = str(uuid.uuid4())

    def test_slippage_prediction_flow_integration(self):
        # Генерируем случайные рыночные параметры
        ticker = random.choice(["AAPL", "TSLA", "BTC-USD", "NVDA"])
        volume = random.uniform(10000, 1000000)
        volatility = random.uniform(0.01, 0.05)

        # Выполняем предсказание через реальные модули
        prediction_result = self.predictor.predict(
            run_id=self.test_run_id,
            ticker=ticker,
            volume=volume,
            volatility=volatility
        )

        # Проверка структуры ответа
        self.assertIn("slippage_estimate", prediction_result)
        self.assertIn("confidence_interval", prediction_result)
        self.assertEqual(prediction_result["run_id"], self.test_run_id)

        # Проверка записи в БД (интеграция с хранилищем)
        stored_data = self.db.get_record(self.test_run_id)
        self.assertIsNotNone(stored_data, "Данные не были записаны в DBStorage")
        self.assertEqual(stored_data["ticker"], ticker)
        self.assertAlmostEqual(stored_data["volume"], volume)

        # Проверка влияния на модель ликвидности
        liquidity_state = self.liquidity_analyzer.get_current_depth(ticker)
        self.assertIsInstance(liquidity_state, dict)
        self.assertIn("bid_ask_spread", liquidity_state)

    def test_persistence_and_audit_trail(self):
        # Проверка создания артефакта (файла лога)
        log_filename = f"slippage_audit_{self.test_run_id}.log"

        self.predictor.execute_and_log(
            run_id=self.test_run_id,
            payload={"ticker": "ETH-USD", "amount": random.randint(1, 500)}
        )

        self.assertTrue(os.path.exists(log_filename), f"Файл аудита {log_filename} не был создан")

        # Очистка после теста
        if os.path.exists(log_filename):
            os.remove(log_filename)

if __name__ == "__main__":
    unittest.main()