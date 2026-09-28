import unittest
import uuid
import random
import os
from skills.market_portfolio_tail_risk_analyzer import MarketPortfolioTailRiskAnalyzer
from market_portfolio_valuation import MarketPortfolioValuation
from market_portfolio_collector_agent import MarketPortfolioCollectorAgent
from db_storage import DBStorage

class TestMarketPortfolioTailRiskAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.analyzer = MarketPortfolioTailRiskAnalyzer()
        self.valuation = MarketPortfolioValuation()
        self.collector = MarketPortfolioCollectorAgent()
        self.db = DBStorage()
        self.portfolio_id = str(uuid.uuid4())
        self.test_assets = ["AAPL", "TSLA", "BTC-USD", "GOLD"]

    def test_tail_risk_calculation_flow(self):
        # 1. Генерируем случайные рыночные данные через коллектор
        raw_data = {
            "portfolio_id": self.portfolio_id,
            "assets": self.test_assets,
            "timestamp": random.randint(1600000000, 1700000000)
        }
        self.collector.collect_market_data(raw_data)
        
        # 2. Получаем оценку портфеля для анализа
        valuation_result = self.valuation.calculate_current_value(self.portfolio_id)
        self.assertIsNotNone(valuation_result, "Valuation failed to return data")

        # 3. Выполняем анализ хвостовых рисков
        # Модуль должен прочитать данные из DBStorage, записанные коллектором
        risk_metrics = self.analyzer.analyze(
            portfolio_id=self.portfolio_id,
            confidence_level=0.95,
            lookback_period=random.randint(30, 365)
        )

        # 4. Проверка корректности возвращаемых данных
        self.assertIn("var", risk_metrics)
        self.assertIn("cvar", risk_metrics)
        self.assertLess(risk_metrics["var"], 0, "VaR should represent potential loss")
        self.assertLess(risk_metrics["cvar"], risk_metrics["var"], "CVaR should be more conservative than VaR")

        # 5. Проверка записи результата в БД (интеграция с хранилищем)
        report_id = str(uuid.uuid4())
        self.db.save_report(report_id, risk_metrics)
        
        stored_report = self.db.get_report(report_id)
        self.assertEqual(stored_report["var"], risk_metrics["var"])
        self.assertEqual(stored_report["cvar"], risk_metrics["cvar"])

    def test_empty_portfolio_handling(self):
        # Проверка поведения при передаче несуществующего ID
        random_id = str(uuid.uuid4())
        with self.assertRaises(Exception):
            self.analyzer.analyze(portfolio_id=random_id)

if __name__ == '__main__':
    unittest.main()