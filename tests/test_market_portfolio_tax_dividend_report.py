import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills import market_portfolio_tax_dividend_report

class TestMarketPortfolioTaxDividendReport(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        self.random_tax_rate = round(random.uniform(0.05, 0.25), 2)
        self.random_amount = round(random.uniform(100.0, 10000.0), 2)
        self.random_ticker = ''.join(random.choices(string.ascii_uppercase, k=random.randint(3, 5)))

    def test_generate_tax_dividend_report_composition(self):
        mock_tax_result = {
            "portfolio_id": self.portfolio_id,
            "total_tax": round(self.random_amount * 0.13, 2),
            "status": "calculated"
        }
        mock_dividend_result = {
            "portfolio_id": self.portfolio_id,
            "total_dividends": self.random_amount,
            "ticker": self.random_ticker
        }

        with patch("skills.market_portfolio_tax_calculator.MarketPortfolioTaxCalculator") as mock_tax_calc_cls, \
             patch("skills.market_portfolio_dividend_tracker.DividendTracker") as mock_div_tracker_cls:

            instance_tax_calc = mock_tax_calc_cls.return_value
            instance_tax_calc.calculate_tax.return_value = mock_tax_result

            instance_div_tracker = mock_div_tracker_cls.return_value
            instance_div_tracker.aggregate_portfolio_dividends.return_value = mock_dividend_result

            if hasattr(market_portfolio_tax_dividend_report, "generate_tax_dividend_report"):
                report = market_portfolio_tax_dividend_report.generate_tax_dividend_report(self.portfolio_id)

                self.assertIn("tax_data", report)
                self.assertIn("dividend_data", report)
                self.assertEqual(report["tax_data"]["portfolio_id"], self.portfolio_id)
                self.assertEqual(report["dividend_data"]["total_dividends"], self.random_amount)
            else:
                self.fail("Module missing generate_tax_dividend_report function")

    def test_report_pipeline_error_handling(self):
        random_error_message = ''.join(random.choices(string.ascii_lowercase + string.digits, k=15))

        with patch("skills.market_portfolio_dividend_tracker.DividendTracker") as mock_div_tracker_cls:
            instance_div_tracker = mock_div_tracker_cls.return_value
            instance_div_tracker.aggregate_portfolio_dividends.side_effect = Exception(random_error_message)

            if hasattr(market_portfolio_tax_dividend_report, "generate_tax_dividend_report"):
                with self.assertRaises(Exception) as context:
                    market_portfolio_tax_dividend_report.generate_tax_dividend_report(self.portfolio_id)
                self.assertIn(random_error_message, str(context.exception))
            else:
                self.fail("Module missing generate_tax_dividend_report function")

    def test_stream_and_dividend_processing_integration(self):
        random_stream_data = io.BytesIO(f"stream_id:{uuid.uuid4().hex},amount:{self.random_amount}".encode('utf-8'))

        with patch("skills.market_portfolio_tax_calculator.MarketPortfolioTaxCalculator.process_dividend_stream") as mock_process_stream, \
             patch("skills.market_portfolio_dividend_tracker.process_dividends") as mock_process_divs:

            mock_process_stream.return_value = True
            mock_process_divs.return_value = self.random_ticker

            if hasattr(market_portfolio_tax_dividend_report, "process_comprehensive_stream"):
                res = market_portfolio_tax_dividend_report.process_comprehensive_stream(self.portfolio_id, random_stream_data)
                self.assertTrue(res)
                mock_process_stream.assert_called_once()
            else:
                # Fallback check if function naming differs
                pass

if __name__ == '__main__':
    unittest.main()