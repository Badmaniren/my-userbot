import unittest
import uuid
import random
import os
from skills.market_portfolio_macro_liquidity_tracker import market_portfolio_macro_liquidity_tracker
from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent

class TestMarketPortfolioMacroLiquidityTrackerIntegration(unittest.TestCase):
    def test_macro_liquidity_tracker_flow(self):
        portfolio_id = str(uuid.uuid4())
        liquidity_score = round(random.uniform(10500.50, 999999.99), 2)
        
        # Подготовка реальных данных через связанный модуль без моков
        collector_payload = {
            "portfolio_id": portfolio_id,
            "liquidity_metric": liquidity_score,
            "source": "integration_test"
        }
        
        collection_result = market_portfolio_collector_agent(collector_payload)
        self.assertIsNotNone(collection_result)

        # Вызов тестируемого модуля макроликвидности
        tracker_input = {
            "portfolio_id": portfolio_id,
            "target_liquidity": liquidity_score
        }
        tracking_output = market_portfolio_macro_liquidity_tracker(tracker_input)
        
        # Проверяем возврат конкретных случайных ID и реальных данных
        self.assertIsInstance(tracking_output, dict)
        self.assertEqual(tracking_output.get("portfolio_id"), portfolio_id)
        self.assertIn("status", tracking_output)

        # Проверка сохранения в реальное хранилище данных (db_storage)
        stored_data = db_storage({"action": "get", "portfolio_id": portfolio_id})
        self.assertIsNotNone(stored_data)

        # Проверка появления артефактов/логов на диске, если применимо
        log_file_path = f"logs/macro_liquidity_{portfolio_id}.log"
        if os.path.exists(log_file_path):
            self.assertTrue(os.path.getsize(log_file_path) > 0)

if __name__ == "__main__":
    unittest.main()