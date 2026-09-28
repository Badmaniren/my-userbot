import unittest
import uuid
import random
import os
import sys

skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'skills'))
if skills_dir not in sys.path:
    sys.path.insert(0, skills_dir)

from skills.market_portfolio_tail_risk_analyzer import MarketPortfolioTailRiskAnalyzer
from skills.market_portfolio_hedge_allocator import MarketPortfolioHedgeAllocator
try:
    from skills.db_storage import DBStorage
except ImportError:
    from db_storage import DBStorage


class TestMarketPortfolioHedgeAllocatorIntegration(unittest.TestCase):
    def setUp(self):
        self.db = DBStorage()
        self.analyzer = MarketPortfolioTailRiskAnalyzer()
        self.allocator = MarketPortfolioHedgeAllocator()
        self.portfolio_id = str(uuid.uuid4())
        self.test_assets = ["AAPL", "TSLA", "BTC", "GLD"]

    def test_hedge_allocation_flow(self):
        # 1. Генерация случайных рыночных данных для анализа
        market_data = {
            "portfolio_id": self.portfolio_id,
            "assets": self.test_assets,
            "volatility": random.uniform(0.1, 0.5),
            "confidence_level": 0.95
        }

        # 2. Вызов анализатора (реальный расчет VaR/CVaR)
        risk_metrics = self.analyzer.calculate_tail_risk(market_data)
        self.assertIn("var", risk_metrics)
        self.assertIn("cvar", risk_metrics)

        # 3. Вызов аллокатора (интеграция без моков)
        allocation_plan = self.allocator.calculate_hedge_strategy(
            portfolio_id=self.portfolio_id,
            risk_metrics=risk_metrics
        )

        # 4. Проверка корректности возвращаемых данных
        self.assertEqual(allocation_plan["portfolio_id"], self.portfolio_id)
        self.assertIsInstance(allocation_plan["hedge_assets"], list)
        self.assertTrue(len(allocation_plan["hedge_assets"]) > 0)

        # 5. Проверка записи в БД (реальный эффект)
        self.db.save_allocation(allocation_plan)
        stored_data = self.db.get_allocation(self.portfolio_id)

        self.assertEqual(stored_data["portfolio_id"], self.portfolio_id)
        self.assertEqual(stored_data["cvar"], risk_metrics["cvar"])

        # 6. Проверка создания артефакта (лог-файл или отчет)
        report_path = f"hedge_report_{self.portfolio_id}.json"
        self.assertTrue(os.path.exists(report_path) or self.db.check_exists(report_path))

        if os.path.exists(report_path):
            os.remove(report_path)


if __name__ == "__main__":
    unittest.main()
