import unittest
import os
import uuid
import random
from skills.market_portfolio_risk_dashboard import MarketPortfolioRiskDashboard, generate_risk_dashboard

class TestMarketPortfolioRiskDashboardIntegration(unittest.TestCase):
    def setUp(self):
        self.unique_id = uuid.uuid4().hex[:8]
        self.storage_file = f"test_portfolio_storage_{self.unique_id}.json"
        self.symbol = f"SYM{random.randint(100, 999)}"

        # Подготовка фейкового файла хранилища для реальной интеграции
        with open(self.storage_file, "w", encoding="utf-8") as f:
            f.write("{}")

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_risk_dashboard_integration(self):
        dashboard_result = generate_risk_dashboard(self.storage_file, self.symbol)

        self.assertIsNotNone(dashboard_result)
        self.assertTrue(
            isinstance(dashboard_result, (str, dict)),
            "Результат дашборда должен быть строкой или словарем"
        )

        if isinstance(dashboard_result, str):
            self.assertIn(self.symbol, dashboard_result)

        instance = MarketPortfolioRiskDashboard(self.storage_file)
        self.assertEqual(instance.storage_file, self.storage_file)

        obj_result = instance.generate_dashboard(self.symbol)
        self.assertEqual(dashboard_result, obj_result)

if __name__ == "__main__":
    unittest.main()