import unittest
import os
import uuid
import json
import io
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core, start_new

class TestMarketPortfolioVarLiquidityCoreIntegration(unittest.TestCase):
    def setUp(self):
        self.core_class = market_portfolio_var_liquidity_core()
        self.portfolio_id = f"port_{uuid.uuid4().hex}"
        self.confidence_level = round(0.90 + (uuid.uuid4().int % 10) / 100.0, 2)
        self.export_filename = f"export_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.export_filename):
            try:
                os.remove(self.export_filename)
            except OSError:
                pass

    def test_calculate_var_and_liquidity_integration(self):
        result = self.core_class.calculate_var_and_liquidity(
            portfolio_id=self.portfolio_id,
            confidence_level=self.confidence_level,
            export_target=self.export_filename
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("var_value", result)
        self.assertIn("liquidity_score", result)

        self.assertTrue(os.path.exists(self.export_filename), "Файл экспорта не был создан")
        
        with open(self.export_filename, "r", encoding="utf-8") as f:
            file_data = json.load(f)
            
        self.assertEqual(file_data.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(file_data.get("var_value"), result["var_value"])
        self.assertEqual(file_data.get("liquidity_score"), result["liquidity_score"])

    def test_start_new_io_bytes_handling(self):
        random_text = f"data_stream_{uuid.uuid4().hex}"
        byte_stream = io.BytesIO(random_text.encode('utf-8'))
        
        output = start_new(payload_stream=byte_stream)
        self.assertEqual(output, random_text)

    def test_start_new_db_storage_handling(self):
        db_mock_identifier = f"storage_{uuid.uuid4().hex}"
        output = start_new(db_storage=db_mock_identifier)
        self.assertEqual(output, db_mock_identifier)

if __name__ == "__main__":
    unittest.main()