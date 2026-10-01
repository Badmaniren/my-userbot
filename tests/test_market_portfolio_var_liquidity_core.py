import unittest
from unittest.mock import patch
import io
import json
import os
import random
import uuid
import string

from skills.market_portfolio_var_liquidity_core import start_new, market_portfolio_var_liquidity_core


class TestMarketPortfolioVarLiquidityCore(unittest.TestCase):

    def test_start_new_default_success(self):
        random_noise_args = {
            "".join(random.choices(string.ascii_lowercase, k=8)): "".join(random.choices(string.ascii_lowercase, k=12))
            for _ in range(random.randint(1, 3))
        }
        result = start_new(**random_noise_args)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")

    def test_start_new_bytes_io_stream(self):
        random_content = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        stream_key = "".join(random.choices(string.ascii_lowercase, k=6))
        byte_stream = io.BytesIO(random_content.encode('utf-8'))

        kwargs = {stream_key: byte_stream}
        output = start_new(**kwargs)
        self.assertEqual(output, random_content)

    def test_start_new_db_storage(self):
        storage_payload = {
            "node_id": uuid.uuid4().hex,
            "metrics": [random.random() for _ in range(3)]
        }
        kwargs = {"db_storage": storage_payload}
        output = start_new(**kwargs)
        self.assertEqual(output, storage_payload)

    def test_start_new_portfolio_calculation(self):
        portfolio_id = uuid.uuid4().hex
        confidence = round(random.uniform(0.80, 0.99), 2)
        
        expected_var = round(1500.50 * confidence, 2)
        expected_liquidity = 0.85

        result = start_new(portfolio_id=portfolio_id, confidence_level=confidence)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("var_value"), expected_var)
        self.assertEqual(result.get("liquidity_score"), expected_liquidity)

    def test_start_new_portfolio_with_export(self):
        portfolio_id = uuid.uuid4().hex
        confidence = round(random.uniform(0.85, 0.98), 2)
        export_filename = f"{uuid.uuid4().hex}.json"

        try:
            result = start_new(
                portfolio_id=portfolio_id,
                confidence_level=confidence,
                export_target=export_filename
            )

            self.assertTrue(os.path.exists(export_filename))
            with open(export_filename, "r", encoding="utf-8") as f:
                file_data = json.load(f)

            self.assertEqual(file_data.get("portfolio_id"), portfolio_id)
            self.assertEqual(file_data.get("var_value"), result.get("var_value"))
            self.assertEqual(file_data.get("liquidity_score"), result.get("liquidity_score"))
        finally:
            if os.path.exists(export_filename):
                os.remove(export_filename)

    def test_class_method_var_and_liquidity(self):
        core_instance = market_portfolio_var_liquidity_core()
        portfolio_id = uuid.uuid4().hex
        confidence = round(random.uniform(0.80, 0.99), 2)

        result = core_instance.calculate_var_and_liquidity(
            portfolio_id=portfolio_id,
            confidence_level=confidence
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertIn("var_value", result)
        self.assertIn("liquidity_score", result)


if __name__ == '__main__':
    unittest.main()