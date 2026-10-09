import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.market_portfolio_stress_auto_hedge_sync import MarketPortfolioStressAutoHedgeSync

class TestMarketPortfolioStressAutoHedgeSync(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.request_id = uuid.uuid4().hex
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.percentage = random.uniform(0.01, 0.99)
        self.shifts = [random.uniform(-0.1, 0.1) for _ in range(3)]
        
        self.mock_db = MagicMock()
        self.mock_monitor = MagicMock()
        self.mock_evaluator = MagicMock()
        self.mock_rebalancer = MagicMock()
        self.mock_advisor = MagicMock()
        self.mock_pipeline = MagicMock()

    def test_synchronize_execution_flow(self):
        # Генерируем случайные ответы для моков
        expected_advisor_res = {"decision": uuid.uuid4().hex, "risk_score": random.random()}
        expected_pipeline_res = {"execution_id": uuid.uuid4().hex, "status": "executed"}

        with patch('skills.market_portfolio_stress_hedge_advisor.MarketPortfolioStressHedgeAdvisor', return_value=self.mock_advisor), \
             patch('skills.market_portfolio_stress_scenario_pipeline.PortfolioStressScenarioPipeline', return_value=self.mock_pipeline):

            self.mock_advisor.analyze_and_recommend.return_value = expected_advisor_res
            self.mock_pipeline.execute.return_value = expected_pipeline_res

            syncer = MarketPortfolioStressAutoHedgeSync(
                db_storage=self.mock_db,
                monitor=self.mock_monitor,
                evaluator=self.mock_evaluator,
                rebalancer=self.mock_rebalancer,
                advisor=self.mock_advisor,
                pipeline=self.mock_pipeline
            )

            result = syncer.synchronize(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            # Проверка целостности данных
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["request_id"], self.request_id)
            self.assertEqual(result["advisor_recommendation"], expected_advisor_res)
            self.assertEqual(result["stress_pipeline_result"], expected_pipeline_res)

            # Проверка вызовов
            self.mock_advisor.analyze_and_recommend.assert_called_once_with(
                portfolio_id=self.portfolio_id,
                request_id=self.request_id
            )
            self.mock_pipeline.execute.assert_called_once_with(
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

    def test_synchronize_dependency_injection_fallback(self):
        # Проверяем, что если advisor не передан, он инициализируется корректно
        # и подхватывает переданные компоненты
        with patch('skills.market_portfolio_stress_hedge_advisor.MarketPortfolioStressHedgeAdvisor') as MockAdvisorClass:
            instance = MarketPortfolioStressAutoHedgeSync(
                db_storage=self.mock_db,
                monitor=self.mock_monitor,
                rebalancer=self.mock_rebalancer
            )

            # Проверяем, что конструктор Advisor был вызван с нашими моками
            MockAdvisorClass.assert_called_once()
            args, kwargs = MockAdvisorClass.call_args
            self.assertEqual(kwargs['monitor'], self.mock_monitor)
            self.assertEqual(kwargs['rebalancer'], self.mock_rebalancer)

    def test_synchronize_runtime_attribute_patching(self):
        # Проверяем логику "самолечения" атрибутов в методе synchronize
        syncer = MarketPortfolioStressAutoHedgeSync(
            advisor=self.mock_advisor,
            monitor=self.mock_monitor,
            rebalancer=self.mock_rebalancer
        )
        
        # Умышленно зануляем атрибуты, чтобы проверить их восстановление
        self.mock_advisor.monitor = None
        self.mock_advisor.rebalancer = None

        self.mock_advisor.analyze_and_recommend.return_value = {}
        self.mock_pipeline.execute.return_value = {}
        syncer.pipeline = self.mock_pipeline

        syncer.synchronize(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertEqual(self.mock_advisor.monitor, self.mock_monitor)
        self.assertEqual(self.mock_advisor.rebalancer, self.mock_rebalancer)

if __name__ == '__main__':
    unittest.main()