import unittest
import uuid
import random
import os
from skills.market_macro_liquidity_collector import market_macro_liquidity_collector
from skills.db_storage import db_storage
from skills.market_parser import market_parser

class TestMarketMacroLiquidityCollectorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_id = str(uuid.uuid4())
        self.random_factor = random.uniform(1000.0, 99999.0)
        self.db = db_storage()
        self.parser = market_parser()
        self.collector = market_macro_liquidity_collector()

    def test_macro_liquidity_collection_pipeline_integration(self):
        payload = {
            "run_id": self.test_id,
            "liquidity_index": self.random_factor,
            "source": "integration_test_suite"
        }

        parsed_data = self.parser.parse(payload)
        self.assertIsNotNone(parsed_data)

        collection_result = self.collector.collect(parsed_data)
        self.assertIn("status", collection_result)
        self.assertEqual(collection_result["status"], "success")
        self.assertEqual(collection_result["run_id"], self.test_id)

        stored_record = self.db.get_record(self.test_id)
        self.assertIsNotNone(stored_record)
        self.assertEqual(stored_record["run_id"], self.test_id)
        self.assertEqual(float(stored_record["liquidity_index"]), self.random_factor)

    def tearDown(self):
        if hasattr(self.db, "cleanup"):
            self.db.cleanup(self.test_id)

if __name__ == "__main__":
    unittest.main()