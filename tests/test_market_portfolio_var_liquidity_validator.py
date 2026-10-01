import unittest
from unittest.mock import patch
import io
import uuid

from skills.market_portfolio_var_liquidity_validator import start_new, market_portfolio_var_liquidity_validator


class TestMarketPortfolioVarLiquidityValidator(unittest.TestCase):

    def setUp(self):
        self.validator_instance = market_portfolio_var_liquidity_validator()

    def test_start_new_bytes_io_handling(self):
        random_bytes = f"data_{uuid.uuid4().hex}".encode('utf-8')
        stream = io.BytesIO(random_bytes)
        result = start_new(stream=stream)
        self.assertEqual(result, random_bytes.decode('utf-8'))

    def test_start_new_db_storage(self):
        storage_val = uuid.uuid4().hex
        result = start_new(db_storage=storage_val)
        self.assertEqual(result, storage_val)

    def test_start_new_default(self):
        result = start_new()
        self.assertEqual(result, {"status": "success"})

    def test_audit_calculation_success(self):
        portfolio_data = {
            "portfolio_id": "TEST_PORT",
            "positions": [
                {
                    "ticker": "AAPL",
                    "asset_class": "equity",
                    "market_value": 10000.0,
                    "daily_volume": 1000000.0,
                    "liquidity_score": 0.95
                }
            ]
        }
        core_result = {
            "nominal_var": 500.0,
            "liquid_var": 550.0,
            "liquidity_adjustment": 50.0
        }

        report = self.validator_instance.audit_calculation(portfolio_data, core_result)
        self.assertEqual(report["status"], "PASSED")
        self.assertEqual(report["liquidity_risk_grade"], "LOW")
        self.assertEqual(len(report["position_breakdowns"]), 1)

    def test_audit_calculation_invalid_input(self):
        report = self.validator_instance.audit_calculation(None, None)
        self.assertEqual(report["status"], "FAILED")


if __name__ == '__main__':
    unittest.main()