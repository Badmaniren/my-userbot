import unittest
import sys
import os
import uuid
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'skills')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from skills.market_portfolio_hedge_trigger import MarketPortfolioHedgeTrigger
from market_portfolio_valuation import MarketPortfolioValuation
from market_portfolio_stress_scenario_pipeline import MarketPortfolioStressScenarioPipeline
from db_storage import DBStorage

class TestMarketPortfolioHedgeTriggerIntegration(unittest.TestCase):
    def setUp(self):
        self.db = DBStorage()
        self.valuation = MarketPortfolioValuation()
        self.stress_pipeline = MarketPortfolioStressScenarioPipeline()
        self.trigger = MarketPortfolioHedgeTrigger(
            db_storage=self.db,
            valuation=self.valuation,
            stress_pipeline=self.stress_pipeline
        )
        self.portfolio_id = str(uuid.uuid4())
        self.risk_threshold = random.uniform(0.01, 0.05)

    def test_hedge_trigger_lifecycle(self):
        # 1. Подготовка данных через реальные модули
        mock_assets = {"AAPL": random.randint(10, 100), "TSLA": random.randint(5, 50)}
        self.db.save_portfolio(self.portfolio_id, mock_assets)

        # 2. Получение оценки портфеля
        valuation_data = self.valuation.calculate_current_value(self.portfolio_id)
        self.assertIsNotNone(valuation_data, "Valuation module failed to return data")

        # 3. Генерация стресс-сценария
        scenario_id = str(uuid.uuid4())
        stress_metrics = self.stress_pipeline.run_stress_test(self.portfolio_id, scenario_id)
        self.assertIn('cvar', stress_metrics, "Stress pipeline failed to calculate CVaR")

        # 4. Вызов целевого модуля (Интеграция)
        result = self.trigger.determine_hedge_signal(
            portfolio_id=self.portfolio_id,
            cvar=stress_metrics['cvar'],
            threshold=self.risk_threshold
        )

        # 5. Проверка реальных изменений
        self.assertIn('activation_signal', result)
        self.assertIn('coverage_ratio', result)

        # Проверка записи в БД через реальный модуль
        stored_signal = self.db.get_latest_hedge_signal(self.portfolio_id)
        self.assertEqual(stored_signal['signal_id'], result['signal_id'], "Signal ID mismatch in DB")
        self.assertTrue(isinstance(result['coverage_ratio'], float))

    def tearDown(self):
        self.db.delete_portfolio(self.portfolio_id)

if __name__ == '__main__':
    unittest.main()