import unittest
from unittest.mock import patch
import io
import json
import os
import random
import uuid
from skills.market_portfolio_var_liquidity_core import start_new, market_portfolio_var_liquidity_core

class TestMarketPortfolioVarLiquidityCore(unittest.TestCase):

    def setUp(self):
        self.instance = market_portfolio_var_liquidity_core()
        self.random_portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.random_confidence = round(random.uniform(0.80, 0.99), 2)
        self.random_db_storage = f"db_{uuid.uuid4().hex}"
        self.random_bytes_content = f"data_{uuid.uuid4().hex}".encode('utf-8')
        self.random_export_target = f"export_{uuid.uuid4().hex[:6]}.json"

    def tearDown(self):
        if os.path.exists(self.random_export_target):
            try:
                os.remove(self.random_export_target)
            except OSError:
                pass

    def test_start_new_default_success(self):
        res = start_new()
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "success")

    def test_start_new_bytes_io_handling(self):
        byte_stream = io.BytesIO(self.random_bytes_content)
        res = start_new(payload=byte_stream)
        self.assertEqual(res, self.random_bytes_content.decode('utf-8'))

    def test_start_new_db_storage_handling(self):
        res = start_new(db_storage=self.random_db_storage)
        self.assertEqual(res, self.random_db_storage)

    def test_start_new_portfolio_calculation(self):
        res = start_new(portfolio_id=self.random_portfolio_id, confidence_level=self.random_confidence)
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), self.random_portfolio_id)
        expected_var = round(1500.50 * self.random_confidence, 2)
        self.assertEqual(res.get("var_value"), expected_var)
        self.assertIn("liquidity_score", res)

    def test_start_new_portfolio_with_export(self):
        res = start_new(
            portfolio_id=self.random_portfolio_id,
            confidence_level=self.random_confidence,
            export_target=self.random_export_target
        )
        self.assertIsInstance(res, dict)
        self.assertTrue(os.path.exists(self.random_export_target))
        with open(self.random_export_target, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("portfolio_id"), self.random_portfolio_id)
        self.assertEqual(data.get("var_value"), round(1500.50 * self.random_confidence, 2))

    def test_class_calculate_var_and_liquidity(self):
        res = self.instance.calculate_var_and_liquidity(
            portfolio_id=self.random_portfolio_id,
            confidence_level=self.random_confidence,
            export_target=None
        )
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("portfolio_id"), self.random_portfolio_id)
        self.assertEqual(res.get("liquidity_score"), 0.85)

    def test_class_calculate_var_and_liquidity_with_export(self):
        res = self.instance.calculate_var_and_liquidity(
            portfolio_id=self.random_portfolio_id,
            confidence_level=self.random_confidence,
            export_target=self.random_export_target
        )
        self.assertIsInstance(res, dict)
        self.assertTrue(os.path.exists(self.random_export_target))

    def test_start_new_with_multiple_random_kwargs(self):
        extra_key = f"key_{uuid.uuid4().hex[:4]}"
        extra_val = f"val_{uuid.uuid4().hex[:4]}"
        kwargs = {
            "portfolio_id": self.random_portfolio_id,
            "confidence_level": self.random_confidence,
            extra_key: extra_val
        }
        res = start_new(**kwargs)
        self.assertEqual(res.get("portfolio_id"), self.random_portfolio_id)

    def test_db_storage_priority_over_portfolio(self):
        res = start_new(
            db_storage=self.random_db_storage,
            portfolio_id=self.random_portfolio_id,
            confidence_level=self.random_confidence
        )
        self.assertEqual(res, self.random_db_storage)

if __name__ == "__main__":
    unittest.main()