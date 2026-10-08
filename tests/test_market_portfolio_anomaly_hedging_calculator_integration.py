import unittest
import random
import uuid
import os
from skills.db_storage import DbStorage
from skills.market_anomaly_detector import MarketAnomalyDetector
from skills.market_insider_activity_tracker import MarketInsiderActivityTracker
from skills.market_portfolio_valuation import MarketPortfolioValuation
from skills.market_portfolio_anomaly_hedging_calculator import MarketPortfolioAnomalyHedgingCalculator

class TestMarketPortfolioAnomalyHedgingCalculatorIntegration(unittest.TestCase):
    def setUp(self):
        # Инициализируем уникальный файл базы данных для интеграционного теста
        self.db_path = f"test_integration_{uuid.uuid4().hex}.db"
        self.db_storage = DbStorage(db_path=self.db_path)

        # Инициализируем реальные связанные модули без использования моков
        self.anomaly_detector = MarketAnomalyDetector(db_storage=self.db_storage)
        self.insider_tracker = MarketInsiderActivityTracker(db_storage=self.db_storage)
        self.portfolio_valuation = MarketPortfolioValuation(db_storage=self.db_storage)

        # Инициализируем тестируемый модуль
        self.calculator = MarketPortfolioAnomalyHedgingCalculator(
            db_storage=self.db_storage,
            anomaly_detector=self.anomaly_detector,
            insider_tracker=self.insider_tracker,
            portfolio_valuation=self.portfolio_valuation
        )

    def tearDown(self):
        # Закрываем соединение и удаляем временный файл БД
        if hasattr(self, 'db_storage'):
            self.db_storage.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_calculate_hedging_parameters_integration(self):
        # Генерация случайных входных данных для исключения хардкода
        portfolio_id = f"portfolio_{uuid.uuid4().hex}"
        asset_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"

        portfolio_value = round(random.uniform(1000000.0, 50000000.0), 2)
        asset_weight = round(random.uniform(0.05, 0.35), 4)
        asset_beta = round(random.uniform(0.5, 2.5), 2)
        anomaly_score = round(random.uniform(0.70, 0.99), 2)
        insider_volume = round(random.uniform(50000.0, 1500000.0), 2)

        # 1. Записываем реальные данные в модуль оценки портфеля
        self.portfolio_valuation.save_portfolio_valuation(
            portfolio_id=portfolio_id,
            total_value=portfolio_value,
            asset_allocations={asset_ticker: asset_weight}
        )

        # 2. Записываем реальные данные в детектор аномалий
        self.anomaly_detector.register_anomaly(
            asset_ticker=asset_ticker,
            anomaly_score=anomaly_score,
            anomaly_type="VOLUME_SPIKE"
        )

        # 3. Записываем реальные данные в трекер инсайдерской активности
        self.insider_tracker.log_insider_transaction(
            asset_ticker=asset_ticker,
            transaction_type="SELL",
            volume=insider_volume,
            insider_role="DIRECTOR"
        )

        # 4. Вызываем тестируемый метод интеграционного калькулятора хеджирования
        result = self.calculator.calculate_hedging_parameters(
            portfolio_id=portfolio_id,
            anomalous_asset=asset_ticker,
            asset_beta=asset_beta
        )

        # 5. Проверяем корректность возвращенных данных и интеграцию
        self.assertIsNotNone(result)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["anomalous_asset"], asset_ticker)
        self.assertEqual(result["beta_sensitivity"], asset_beta)

        # Проверяем, что расчеты произведены на основе случайных входных данных
        self.assertGreater(result["required_hedge_volume"], 0)
        self.assertGreater(result["risk_factor"], 0)

        # Ожидаемый объем хеджирования зависит от стоимости актива в портфеле и беты
        expected_asset_value = portfolio_value * asset_weight
        expected_base_hedge = expected_asset_value * asset_beta
        # Проверяем, что калькулятор учел аномалии и инсайдерскую активность (risk_factor > 1.0)
        self.assertGreaterEqual(result["required_hedge_volume"], expected_base_hedge)

        # 6. Проверяем реальные изменения в базе данных (сохранение результатов расчета)
        saved_calculation = self.db_storage.get_hedging_calculation(portfolio_id, asset_ticker)
        self.assertIsNotNone(saved_calculation)
        self.assertEqual(saved_calculation["portfolio_id"], portfolio_id)
        self.assertEqual(saved_calculation["anomalous_asset"], asset_ticker)
        self.assertAlmostEqual(saved_calculation["required_hedge_volume"], result["required_hedge_volume"], places=2)

if __name__ == "__main__":
    unittest.main()