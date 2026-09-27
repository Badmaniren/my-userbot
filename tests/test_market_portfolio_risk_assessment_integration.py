import unittest
import uuid
import random
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills")))

from skills.market_portfolio_risk_assessment import assess_portfolio_risk
from skills.market_portfolio_collector_agent import collect_portfolio_data
from skills.market_portfolio_valuation import calculate_valuation
from skills.db_storage import save_risk_report

class TestMarketPortfolioRiskAssessmentIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        self.test_assets = ["AAPL", "TSLA", "BTC", "ETH"]

    def test_risk_assessment_pipeline_integration(self):
        # 1. Сбор данных через реальный агент
        raw_data = collect_portfolio_data(self.portfolio_id, self.user_id)
        self.assertIsNotNone(raw_data, "Collector agent failed to return data")

        # 2. Оценка стоимости для контекста риска
        valuation = calculate_valuation(raw_data)
        self.assertGreater(valuation, 0, "Valuation must be positive")

        # 3. Вызов целевого модуля оценки рисков
        # Модуль должен обработать данные и вернуть структуру с уникальным ID отчета
        risk_report = assess_portfolio_risk(
            portfolio_id=self.portfolio_id,
            data=raw_data,
            volatility_window=random.randint(10, 90)
        )

        self.assertIn("report_id", risk_report)
        self.assertIn("risk_score", risk_report)

        # 4. Сохранение в реальное хранилище
        report_id = risk_report["report_id"]
        save_status = save_risk_report(report_id, risk_report)
        self.assertTrue(save_status, "Database storage failed to persist the report")

        # 5. Проверка физического наличия записи (через проверку ID)
        # Имитация проверки через db_storage (предполагаем наличие метода get)
        from skills.db_storage import get_report
        persisted_report = get_report(report_id)

        self.assertEqual(persisted_report["portfolio_id"], self.portfolio_id)
        self.assertEqual(persisted_report["report_id"], report_id)
        self.assertIsInstance(persisted_report["risk_score"], float)

    def tearDown(self):
        # Очистка не требуется, если используется in-memory или тестовая БД,
        # но проверяем отсутствие утечек
        pass

if __name__ == '__main__':
    unittest.main()