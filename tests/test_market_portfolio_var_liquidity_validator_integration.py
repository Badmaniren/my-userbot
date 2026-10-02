import unittest
import uuid
from skills.market_portfolio_var_liquidity_validator import market_portfolio_var_liquidity_validator
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core


class TestMarketPortfolioVarLiquidityValidatorIntegration(unittest.TestCase):

    def setUp(self):
        self.validator = market_portfolio_var_liquidity_validator()
        self.core = market_portfolio_var_liquidity_core()

    def test_pipeline_integration(self):
        portfolio_data = {
            "portfolio_id": f"PORT_{uuid.uuid4().hex[:6]}",
            "confidence_level": 0.99,
            "horizon_days": 1,
            "positions": [
                {
                    "ticker": "GAZP",
                    "asset_class": "equity",
                    "market_value": 1000000.0,
                    "daily_volume": 5000000.0,
                    "bid_ask_spread_bps": 10.0,
                    "historical_volatility": 0.25,
                    "liquidity_score": 0.85
                }
            ]
        }

        core_result = self.core.calculate_liquid_var(portfolio_data)
        self.assertEqual(core_result["status"], "success")

        audit_report = self.validator.audit_calculation(portfolio_data, core_result)
        self.assertIn(audit_report["status"], ["PASSED", "WARNING", "FAILED"])
        self.assertEqual(len(audit_report["position_breakdowns"]), 1)


if __name__ == "__main__":
    unittest.main()