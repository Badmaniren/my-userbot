import random
import unittest
import uuid
from skills.market_portfolio_dividend_tracker import (
    DividendTracker,
    DividendTrackerException,
)
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator
from skills.market_portfolio_net_dividend_calculator import (
    NetDividendCalculator,
    NetDividendCalculatorException,
)


class TestMarketPortfolioNetDividendCalculatorIntegration(unittest.TestCase):
    def setUp(self):
        self.tax_calc = MarketPortfolioTaxCalculator()
        self.tracker = DividendTracker(tax_calculator=self.tax_calc)
        self.calculator = NetDividendCalculator(
            dividend_tracker=self.tracker,
            tax_calculator=self.tax_calc
        )

    def test_calculate_net_dividend_yield_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:10]}"
        asset_ticker = f"TCK_{uuid.uuid4().hex[:4].upper()}"
        shares_count = random.randint(10, 500)
        asset_price = round(random.uniform(20.0, 300.0), 2)
        tax_rate = round(random.uniform(0.10, 0.25), 2)

        try:
            result = self.calculator.calculate_net_dividend_yield(
                portfolio_id=portfolio_id,
                asset_ticker=asset_ticker,
                shares_count=shares_count,
                asset_price=asset_price,
                tax_rate=tax_rate
            )
            self.assertIsInstance(result, dict)
            self.assertIn("ticker", result)
            self.assertIn("shares", result)
            self.assertIn("net_dividend_amount", result)
            self.assertIn("net_dividend_yield", result)
            self.assertEqual(result["ticker"], asset_ticker)
            self.assertEqual(result["shares"], shares_count)
            self.assertIsInstance(result["net_dividend_amount"], (int, float))
            self.assertIsInstance(result["net_dividend_yield"], (int, float))
        except NetDividendCalculatorException as e:
            self.assertTrue(len(str(e)) > 0)

    def test_aggregate_net_dividends_for_portfolio_integration(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:10]}"
        try:
            result = self.calculator.aggregate_net_dividends_for_portfolio(portfolio_id)
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("portfolio_id"), portfolio_id)
            self.assertIn("total_net_dividends", result)
            self.assertIsInstance(result["total_net_dividends"], (int, float))
        except NetDividendCalculatorException as e:
            self.assertTrue(len(str(e)) > 0)

    def test_default_instantiation_without_explicit_skills(self):
        calc_default = NetDividendCalculator()
        self.assertIsInstance(calc_default.dividend_tracker, DividendTracker)
        self.assertIsInstance(calc_default.tax_calculator, MarketPortfolioTaxCalculator)

        portfolio_id = f"port_{uuid.uuid4().hex[:10]}"
        try:
            result = calc_default.aggregate_net_dividends_for_portfolio(portfolio_id)
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("portfolio_id"), portfolio_id)
        except NetDividendCalculatorException as e:
            self.assertTrue(len(str(e)) > 0)


if __name__ == "__main__":
    unittest.main()