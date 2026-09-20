import unittest
import os
import uuid
import random
from skills.market_portfolio_predictive_engine import PredictiveEngine
from skills.market_portfolio_collector_agent import MarketParser, PortfolioValuation
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator


class TestMarketPortfolioPredictiveEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_id = str(uuid.uuid4())[:8]
        self.storage_file = f"test_storage_{self.test_id}.json"
        self.symbol = f"TICKER_{self.test_id}"
        self.url = f"http://example.com/market/{self.test_id}"

        # Генерируем случайные финансовые показатели
        self.initial_price = round(random.uniform(10.0, 1000.0), 2)
        self.percentage_shift = round(random.uniform(-25.0, 25.0), 2)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_predictive_engine_composition_integration(self):
        # 1. Используем реальный класс сбора данных из market_portfolio_collector_agent
        collector = MarketParser(self.storage_file)
        collector.fetch_and_store(self.symbol, self.initial_price)

        self.assertTrue(
            os.path.exists(self.storage_file),
            "Файл хранилища не был создан агентом сбора данных."
        )

        # 2. Инициализируем тестируемый модуль предиктивного анализа (композиция)
        engine = PredictiveEngine(self.storage_file)

        # 3. Проверяем интеграцию с MarketParser и PortfolioScenarioSimulator через движок
        prediction_result = engine.predict_future_trend(self.symbol, self.percentage_shift)

        self.assertIsInstance(
            prediction_result,
            dict,
            "Предиктивный движок должен возвращать словарь с результатами."
        )
        self.assertIn(
            "projected_price",
            prediction_result,
            "Результат прогноза должен содержать ключ 'projected_price'."
        )

        # Рассчитываем ожидаемую цену на основе случайного сдвига
        expected_projected_price = round(self.initial_price * (1 + self.percentage_shift / 100.0), 2)
        self.assertEqual(
            prediction_result["projected_price"],
            expected_projected_price,
            "Прогнозируемая цена не совпадает с расчетом сценария на основе реальных данных."
        )

        # 4. Проверяем взаимодействие с PortfolioValuation через композицию
        valuation = PortfolioValuation(self.storage_file)
        summary = valuation.get_total_summary(self.url)

        self.assertIsInstance(
            summary,
            dict,
            "Оценка портфеля должна возвращать словарь."
        )


if __name__ == "__main__":
    unittest.main()