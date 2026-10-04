import unittest
import uuid
import random
import os
import tempfile

from skills.market_portfolio_macro_liquidity_collector import market_portfolio_macro_liquidity_collector
from skills.db_storage import db_storage
from skills.market_portfolio_integration_hub import market_portfolio_integration_hub


class TestMarketPortfolioMacroLiquidityCollectorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.test_dir.name, f"test_db_{uuid.uuid4()}.sqlite")

        self.storage = db_storage()
        if hasattr(self.storage, "initialize"):
            self.storage.initialize(self.db_path)
        elif hasattr(self.storage, "connect"):
            self.storage.connect(self.db_path)

        self.integration_hub = market_portfolio_integration_hub()
        self.collector = market_portfolio_macro_liquidity_collector()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_macro_liquidity_collection_and_integration_flow(self):
        random_central_bank_rate = round(random.uniform(0.0, 7.5), 2)
        random_m2_supply = round(random.uniform(15000.0, 25000.0), 2)
        random_reverse_repo = round(random.uniform(100.0, 1000.0), 2)

        test_session_id = str(uuid.uuid4())
        payload = {
            "session_id": test_session_id,
            "central_bank_rate": random_central_bank_rate,
            "m2_money_supply": random_m2_supply,
            "reverse_repo": random_reverse_repo
        }

        collected_data = self.collector.collect(payload)

        self.assertIsNotNone(collected_data, "Сборщик макропоказателей ликвидности не должен возвращать None")
        self.assertIn("session_id", collected_data)
        self.assertEqual(collected_data["session_id"], test_session_id)
        self.assertEqual(collected_data["central_bank_rate"], random_central_bank_rate)
        self.assertEqual(collected_data["m2_money_supply"], random_m2_supply)
        self.assertEqual(collected_data["reverse_repo"], random_reverse_repo)

        integration_result = self.integration_hub.process_liquidity_data(collected_data)
        self.assertTrue(integration_result, "Интеграционный хаб должен успешно обработать собранные данные")

        if hasattr(self.storage, "save_macro_liquidity"):
            self.storage.save_macro_liquidity(collected_data)
            retrieved_data = self.storage.get_macro_liquidity(test_session_id)
            self.assertIsNotNone(retrieved_data)
            self.assertEqual(retrieved_data.get("session_id"), test_session_id)
            self.assertEqual(retrieved_data.get("m2_money_supply"), random_m2_supply)


if __name__ == "__main__":
    unittest.main()