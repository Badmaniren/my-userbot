import unittest
import uuid
import random
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator
from skills.market_portfolio_dividend_tracker import DividendTracker
from skills.market_portfolio_tax_dividend_synthesis import (
    TaxDividendSynthesizer,
    synthesizer_portfolio_report,
    synthesize_portfolio_report,
    synthesize_portfolio_tax_dividend_report,
    TaxDividendSynthesisException
)

class TestTaxDividendSynthesisIntegration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        self.asset_ticker = f"TICKER_{random.randint(1000, 9999)}"
        self.shares_count = random.randint(10, 500)
        self.tax_rate = round(random.uniform(0.05, 0.25), 2)

        self.tax_calculator = MarketPortfolioTaxCalculator()
        self.dividend_tracker = DividendTracker(tax_calculator=self.tax_calculator)
        self.synthesizer = TaxDividendSynthesizer(
            tax_calculator=self.tax_calculator,
            dividend_tracker=self.dividend_tracker
        )

    def test_consolidated_report_generation_integration(self):
        report = self.synthesizer.generate_consolidated_report(self.portfolio_id)

        self.assertIsInstance(report, dict)
        self.assertIn("portfolio_id", report)
        self.assertEqual(report["portfolio_id"], self.portfolio_id)
        self.assertIn("tax_report", report)
        self.assertIn("dividend_report", report)
        self.assertIn("net_income_after_tax", report)
        self.assertIsInstance(report["net_income_after_tax"], (int, float))

    def test_synthesize_portfolio_report_helper(self):
        report = synthesize_portfolio_report(self.portfolio_id)
        self.assertIsInstance(report, dict)
        self.assertEqual(report["portfolio_id"], self.portfolio_id)
        self.assertIn("net_income_after_tax", report)

    def test_synthesize_portfolio_tax_dividend_report_with_projections(self):
        result = synthesize_portfolio_tax_dividend_report(
            portfolio_id=self.portfolio_id,
            user_id=self.user_id,
            tax_calculator=self.tax_calculator,
            dividend_tracker=self.dividend_tracker,
            asset_ticker=self.asset_ticker,
            shares_count=self.shares_count,
            tax_rate=self.tax_rate
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["user_id"], self.user_id)
        self.assertIn("projected_dividends", result)
        self.assertIn("tax_liability", result)
        self.assertIsNotNone(result["projected_dividends"])

    def test_process_raw_stream(self):
        class MockStream:
            def __init__(self, data):
                self.data = data
            def read(self):
                return self.data

        random_stream_data = f"stream_data_{uuid.uuid4()}".encode('utf-8')
        stream = MockStream(random_stream_data)

        res = self.synthesizer.process_raw_stream(stream)
        self.assertEqual(res, random_stream_data)

        res_none = self.synthesizer.process_raw_stream("not_a_stream")
        self.assertIsNone(res_none)

    def test_exception_handling(self):
        class FaultyTaxCalculator:
            def calculate_tax(self, portfolio_id):
                raise RuntimeError("Database connection failure")

        faulty_synthesizer = TaxDividendSynthesizer(tax_calculator=FaultyTaxCalculator())

        with self.assertRaises(TaxDividendSynthesisException):
            faulty_synthesizer.generate_consolidated_report(self.portfolio_id)

if __name__ == '__main__':
    unittest.main()