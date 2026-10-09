import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_hedge_advisor import MarketPortfolioStressHedgeAdvisor
from market_portfolio_monitor import MarketPortfolioMonitor
from market_portfolio_stress_scenario_matrix_evaluator import MarketPortfolioStressScenarioMatrixEvaluator
from market_portfolio_stress_auto_rebalance_trigger import MarketPortfolioStressAutoRebalanceTrigger
from db_storage import DBStorage

class TestMarketPortfolioStressHedgeAdvisorIntegration(unittest.TestCase):
    def setUp(self):
        self.db = DBStorage()
        self.monitor = MarketPortfolioMonitor()
        self.evaluator = MarketPortfolioStressScenarioMatrixEvaluator()
        self.rebalancer = MarketPortfolioStressAutoRebalanceTrigger()
        self.advisor = MarketPortfolioStressHedgeAdvisor(
            db_storage=self.db,
            monitor=self.monitor,
            evaluator=self.evaluator,
            rebalancer=self.rebalancer
        )
        self.portfolio_id = str(uuid.uuid4())
        self.test_log_path = f"stress_audit_{self.portfolio_id}.log"

    def tearDown(self):
        if os.path.exists(self.test_log_path):
            os.remove(self.test_log_path)

    def test_stress_hedge_recommendation_flow(self):
        # Генерируем случайные рыночные данные для стресс-теста
        current_drawdown = random.uniform(0.15, 0.45)
        volatility_index = random.uniform(20.0, 80.0)
        
        # Инициализация состояния через монитор
        self.monitor.update_portfolio_state(
            portfolio_id=self.portfolio_id,
            drawdown=current_drawdown,
            volatility=volatility_index
        )

        # Вызов целевого модуля (без моков)
        result = self.advisor.analyze_and_recommend(
            portfolio_id=self.portfolio_id,
            request_id=str(uuid.uuid4())
        )

        # Проверка: модуль должен вернуть валидный ID рекомендации
        self.assertIsNotNone(result.get("recommendation_id"))
        self.assertTrue(len(result["recommendation_id"]) > 0)

        # Проверка: данные должны быть записаны в БД
        stored_data = self.db.get_record(self.portfolio_id)
        self.assertIsNotNone(stored_data)
        self.assertEqual(stored_data["last_stress_event_id"], result["recommendation_id"])

        # Проверка: триггер ребалансировки должен получить сигнал
        rebalance_status = self.rebalancer.get_trigger_status(self.portfolio_id)
        self.assertEqual(rebalance_status["action"], "HEDGE_REQUIRED")
        
        # Проверка: создание артефакта (аудит лога)
        self.assertTrue(os.path.exists(self.test_log_path) or self.db.check_audit_exists(result["recommendation_id"]))

    def test_no_action_on_stable_market(self):
        # Случайные данные в пределах нормы
        self.monitor.update_portfolio_state(
            portfolio_id=self.portfolio_id,
            drawdown=0.02,
            volatility=10.0
        )

        result = self.advisor.analyze_and_recommend(
            portfolio_id=self.portfolio_id,
            request_id=str(uuid.uuid4())
        )

        # Проверка: при отсутствии стресса рекомендация не должна генерироваться
        self.assertFalse(result.get("hedge_recommended", False))
        self.assertIsNone(result.get("recommendation_id"))

if __name__ == '__main__':
    unittest.main()