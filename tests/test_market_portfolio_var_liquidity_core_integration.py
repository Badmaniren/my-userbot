import unittest
import os
import uuid
import json
import io
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core, start_new

class TestMarketPortfolioVarLiquidityCoreIntegration(unittest.TestCase):
    def setUp(self):
        self.core = market_portfolio_var_liquidity_core()
        self.portfolio_id = f"port-{uuid.uuid4()}"
        self.confidence_level = round(0.90 + (uuid.uuid4().int % 9) / 100.0, 2)
        self.export_target = f"test_export_{uuid.uuid4()}.json"

    def tearDown(self):
        if os.path.exists(self.export_target):
            try:
                os.remove(self.export_target)
            except OSError:
                pass

    def test_integration_calculation_and_export(self):
        result = self.core.calculate_var_and_liquidity(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_target
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        
        expected_var = round(1500.50 * self.confidence_level, 2)
        self.assertEqual(result.get("var_value"), expected_var)
        self.assertIn("liquidity_score", result)

        self.assertTrue(os.path.exists(self.export_target), "Экспортный файл не был создан")
        
        with open(self.export_target, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data.get("portfolio_id"), self.portfolio_id)
            self.assertEqual(data.get("var_value"), expected_var)

    def test_integration_db_storage_flow(self):
        storage_token = f"db_token_{uuid.uuid4()}"
        res = start_new(db_storage=storage_token, random_param=str(uuid.uuid4()))
        self.assertEqual(res, storage_token)

    def test_integration_bytes_io_stream(self):
        stream_content = f"stream_data_{uuid.uuid4()}"
        byte_stream = io.BytesIO(stream_content.encode('utf-8'))
        res = start_new(payload=byte_stream, random_uuid=str(uuid.uuid4()))
        self.assertEqual(res, stream_content)

if __name__ == '__main__':
    unittest.main()