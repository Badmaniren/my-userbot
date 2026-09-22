import unittest
import os
import tempfile
import uuid
import json
import random

from skills.market_portfolio_alert_filter_router import *
from skills import market_portfolio_alert_dispatcher
from skills import market_portfolio_performance_analytics


class TestMarketPortfolioAlertFilterRouterIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_market_data_{uuid.uuid4()}.json")
        
        self.symbol = f"TEST_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/api/{uuid.uuid4()}"
        self.telegram_token = f"token_{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(100000, 999999))
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.min_threshold = round(random.uniform(10.0, 100.0), 2)
        self.channels = ["telegram", "log"]

        initial_data = {
            self.symbol: [
                {"timestamp": "2023-01-01T00:00:00", "price": 100.0},
                {"timestamp": "2023-01-02T00:00:00", "price": 105.0},
                {"timestamp": "2023-01-03T00:00:00", "price": 102.0}
            ]
        }
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_composition_and_filtering_integration(self):
        analytics_instance = market_portfolio_performance_analytics.PortfolioPerformanceAnalytics(self.storage_file)
        metrics = analytics_instance.calculate_metrics(self.symbol)
        
        self.assertIsInstance(metrics, dict, "Аналитический навык должен возвращать словарь метрик")

        try:
            filter_result = filter_and_route_portfolio_alerts(
                symbol=self.symbol,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file,
                severity_level=self.severity_level,
                min_threshold=self.min_threshold,
                channels=self.channels
            )
        except NameError:
            try:
                filter_result = process_alert_filter_routing(
                    symbol=self.symbol,
                    url=self.url,
                    telegram_token=self.telegram_token,
                    chat_id=self.chat_id,
                    storage_file=self.storage_file,
                    severity_level=self.severity_level,
                    min_threshold=self.min_threshold,
                    channels=self.channels
                )
            except NameError:
                router_cls = getattr(sys.modules[__name__], 'AlertFilterRouter', None)
                if router_cls:
                    router = router_cls(self.storage_file)
                    filter_result = router.route_filtered_alerts(
                        symbol=self.symbol,
                        url=self.url,
                        telegram_token=self.telegram_token,
                        chat_id=self.chat_id,
                        severity_level=self.severity_level,
                        min_threshold=self.min_threshold,
                        channels=self.channels
                    )
                else:
                    self.fail("Не найдены ожидаемые функции или классы для интеграции в market_portfolio_alert_filter_router")

        self.assertIsNotNone(filter_result, "Результат маршрутизации алертов не должен быть пустым")
        
        if isinstance(filter_result, dict):
            self.assertIn("status", filter_result)
        elif isinstance(filter_result, bool):
            self.assertTrue(filter_result)


if __name__ == "__main__":
    unittest.main()