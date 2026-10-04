import unittest
import uuid
import random
from skills.market_macro_liquidity_core_engine import MacroLiquidityCoreEngine, start_new
from skills.db_storage import DBStorage

class TestMarketMacroLiquidityCoreEngineIntegration(unittest.TestCase):
    def test_macro_liquidity_pipeline_and_storage(self):
        engine = MacroLiquidityCoreEngine()

        test_id_val = str(uuid.uuid4())
        random_metric = random.uniform(1000.0, 99999.0)

        payload = {
            "test_id": test_id_val,
            "liquidity_metric": random_metric,
            "source": "integration_test"
        }

        result = engine.process_macro_liquidity_data(payload)

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("processed_id"), test_id_val)

        if hasattr(engine.db, "storage") and isinstance(engine.db.storage, dict):
            self.assertIn(test_id_val, engine.db.storage)
            self.assertEqual(engine.db.storage[test_id_val]["liquidity_metric"], random_metric)

    def test_start_new_exception_handling(self):
        invalid_dependencies = {
            "db_storage": "not_an_object"
        }

        with self.assertRaises(TypeError):
            start_new("http://localhost:8080/invalid_macro_endpoint", invalid_dependencies)

if __name__ == "__main__":
    unittest.main()