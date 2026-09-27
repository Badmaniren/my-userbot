import unittest
import uuid
import random
from skills.market_portfolio_tax_dividend_unifier import (
    TaxDividendUnifier,
    unify_portfolio_yield,
    unifier_pipeline
)
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator
from skills.market_portfolio_dividend_tracker import DividendTracker


class TestMarketPortfolioTaxDividendUnifierIntegration(unittest.TestCase):

    def test_tax_dividend_unifier_pipeline_integration(self):
        portfolio_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        asset_ticker = f"TEST_{random.randint(1000, 9999)}"
        shares_count = random.randint(10, 500)
        tax_rate = round(random.uniform(0.10, 0.25), 2)

        dividend_count = random.randint(1, 5)
        dividend_stream = [
            {"amount": round(random.uniform(50.0, 500.0), 2)}
            for _ in range(dividend_count)
        ]

        pipeline_result = unifier_pipeline(
            portfolio_id=portfolio_id,
            user_id=user_id,
            asset_ticker=asset_ticker,
            shares_count=shares_count,
            tax_rate=tax_rate,
            dividend_stream=dividend_stream
        )

        self.assertIsInstance(pipeline_result, dict)
        self.assertEqual(pipeline_result["portfolio_id"], portfolio_id)
        self.assertEqual(pipeline_result["user_id"], user_id)
        self.assertEqual(pipeline_result["asset_ticker"], asset_ticker)
        self.assertEqual(pipeline_result["shares_count"], shares_count)
        self.assertEqual(pipeline_result["tax_rate"], tax_rate)
        self.assertEqual(pipeline_result["dividend_stream"], dividend_stream)

        expected_total_dividends = sum(item.get("amount", 0.0) for item in dividend_stream)
        expected_total_tax = round(expected_total_dividends * tax_rate, 2)
        expected_net_yield = round(expected_total_dividends - expected_total_tax, 2)

        self.assertAlmostEqual(pipeline_result["total_dividends"], expected_total_dividends, places=2)
        self.assertAlmostEqual(pipeline_result["total_tax"], expected_total_tax, places=2)
        self.assertAlmostEqual(pipeline_result["net_yield"], expected_net_yield, places=2)

    def test_tax_dividend_unifier_class_and_function_integration(self):
        portfolio_id = str(uuid.uuid4())

        tax_calc = MarketPortfolioTaxCalculator()
        div_track = DividendTracker()

        unifier = TaxDividendUnifier(
            tax_calculator=tax_calc,
            dividend_tracker=div_track
        )

        net_yield_result = unifier.calculate_net_yield(portfolio_id)

        self.assertIsInstance(net_yield_result, dict)
        self.assertEqual(net_yield_result["portfolio_id"], portfolio_id)
        self.assertIn("tax_withheld", net_yield_result)
        self.assertIn("gross_dividends", net_yield_result)
        self.assertIn("net_yield", net_yield_result)

        functional_result = unify_portfolio_yield(portfolio_id)

        self.assertIsInstance(functional_result, dict)
        self.assertEqual(functional_result["portfolio_id"], portfolio_id)
        self.assertEqual(functional_result["tax_withheld"], net_yield_result["tax_withheld"])
        self.assertEqual(functional_result["gross_dividends"], net_yield_result["gross_dividends"])
        self.assertEqual(functional_result["net_yield"], net_yield_result["net_yield"])

    def test_process_stream_data_integration(self):
        unifier = TaxDividendUnifier()
        stream_data = {
            "portfolio_id": str(uuid.uuid4()),
            "amount": round(random.uniform(100.0, 1000.0), 2),
            "asset": f"ASSET_{random.randint(100, 999)}"
        }

        success = unifier.process_stream_data(stream_data)
        self.assertTrue(success)


if __name__ == "__main__":
    unittest.main()