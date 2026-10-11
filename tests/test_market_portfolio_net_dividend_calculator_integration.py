import unittest
import uuid
import random
from skills.market_portfolio_net_dividend_calculator import (
    NetDividendCalculator,
    market_portfolio_net_dividend_calculator
)


class TestNetDividendCalculatorIntegration(unittest.TestCase):

    def test_process_integration_pipeline(self):
        portfolio_id = f"PORT-{uuid.uuid4().hex[:6]}"
        gross1 = round(random.uniform(50.0, 200.0), 2)
        gross2 = round(random.uniform(100.0, 300.0), 2)
        rate1 = 0.10
        rate2 = 0.13

        portfolio_data = {
            "portfolio_id": portfolio_id,
            "dividends": [
                {"symbol": "SYM1", "gross_amount": gross1, "withholding_tax_rate": rate1},
                {"symbol": "SYM2", "gross_amount": gross2, "withholding_tax_rate": rate2}
            ]
        }

        calc = NetDividendCalculator()
        result = calc.process(portfolio_data)

        expected_gross = round(gross1 + gross2, 2)
        expected_tax = round(gross1 * rate1 + gross2 * rate2, 2)
        expected_net = round(expected_gross - expected_tax, 2)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("total_gross_dividends"), expected_gross)
        self.assertEqual(result.get("dividend_tax_withheld"), expected_tax)
        self.assertEqual(result.get("total_net_dividends"), expected_net)

    def test_global_instance_process(self):
        portfolio_data = {
            "portfolio_id": "GLOBAL-TEST",
            "dividends": [
                {"gross_amount": 500.0, "withholding_tax_rate": 0.20}
            ]
        }
        result = market_portfolio_net_dividend_calculator.process(portfolio_data)
        self.assertEqual(result["total_net_dividends"], 400.0)


if __name__ == "__main__":
    unittest.main()
