import unittest
import uuid
import random
import os
from skills.market_portfolio_risk_engine import MarketPortfolioRiskEngine
from skills.market_portfolio_api_gateway import MarketPortfolioAPIGateway as MarketPortfolioApiGateway
from skills.db_storage import DBStorage
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics as MarketPortfolioPerformanceAnalytics

class TestMarketPortfolioRiskEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.engine = MarketPortfolioRiskEngine()
        self.gateway = MarketPortfolioApiGateway()
        self.db = DBStorage()
        self.analytics = MarketPortfolioPerformanceAnalytics()
        self.test_portfolio_id = str(uuid.uuid4())

    def test_risk_assessment_lifecycle(self):
        # 1. Подготовка случайных рыночных данных
        mock_assets = [f"TICKER_{random.randint(1000, 9999)}" for _ in range(5)]
        mock_volatility = random.uniform(0.01, 0.5)

        # 2. Инициализация через API Gateway
        portfolio_data = {
            "portfolio_id": self.test_portfolio_id,
            "assets": mock_assets,
            "volatility_threshold": mock_volatility
        }
        self.gateway.register_portfolio(portfolio_data)

        # 3. Вызов целевого модуля (без моков)
        # Оценка риска должна записать результат в БД и вернуть ID отчета
        report_id = self.engine.evaluate_risk(self.test_portfolio_id)

        # 4. Проверка: наличие записи в БД
        stored_report = self.db.get_record(report_id)
        self.assertIsNotNone(stored_report, "Отчет о рисках не был сохранен в БД")
        self.assertEqual(stored_report['portfolio_id'], self.test_portfolio_id)

        # 5. Проверка: корреляция с аналитическим модулем
        performance_metrics = self.analytics.get_metrics(self.test_portfolio_id)
        self.assertIn('drawdown', performance_metrics)

        # 6. Проверка: генерация артефакта (например, лог-файла или отчета)
        expected_filename = f"risk_report_{report_id}.json"
        self.assertTrue(os.path.exists(expected_filename), f"Файл {expected_filename} не был создан")

        # Очистка
        if os.path.exists(expected_filename):
            os.remove(expected_filename)

    def test_risk_engine_anomaly_trigger(self):
        # Проверка реакции на экстремальную волатильность
        extreme_volatility = 0.99
        portfolio_id = str(uuid.uuid4())

        # Прямая запись в хранилище для имитации рыночного состояния
        self.db.save_market_state(portfolio_id, {"volatility": extreme_volatility})

        # Запуск движка
        result = self.engine.evaluate_risk(portfolio_id)

        # Проверка, что движок пометил портфель как высокорисковый
        status = self.db.get_status(portfolio_id)
        self.assertEqual(status, "HIGH_RISK_ALERT")
        self.assertIsInstance(result, str)

        # Очистка созданного файла отчета
        expected_filename = f"risk_report_{result}.json"
        if os.path.exists(expected_filename):
            os.remove(expected_filename)

if __name__ == '__main__':
    unittest.main()