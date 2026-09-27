import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.market_portfolio_tax_dividend_sync import (
    TaxDividendSync,
    TaxDividendSyncException
)


class TestTaxDividendSyncArchitectInquisitor(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.api_gateway = MagicMock()
        self.sync_engine = TaxDividendSync(
            db_storage=self.db_storage,
            api_gateway=self.api_gateway
        )

    def test_sync_net_yield_calculation_success(self):
        portfolio_id = str(uuid.uuid4())
        asset_ticker = ''.join(random.choices(string.ascii_uppercase, k=5))
        shares_count = random.randint(10, 1000)
        tax_rate = round(random.uniform(0.05, 0.25), 2)

        expected_dividends = round(random.uniform(100.0, 5000.0), 2)
        expected_tax = round(expected_dividends * tax_rate, 2)
        expected_net_yield = round(expected_dividends - expected_tax, 2)

        with patch('skills.market_portfolio_dividend_tracker.DividendTracker.calculate_projected_dividends', return_value=expected_dividends) as mock_div_calc, \
             patch('skills.market_portfolio_tax_calculator.MarketPortfolioTaxCalculator.calculate_tax', return_value=expected_tax) as mock_tax_calc:

            result = self.sync_engine.calculate_synchronized_net_yield(
                portfolio_id=portfolio_id,
                asset_ticker=asset_ticker,
                shares_count=shares_count,
                tax_rate=tax_rate
            )

            mock_div_calc.assert_called_once()
            mock_tax_calc.assert_called_once()

            self.assertIn('net_yield', result)
            self.assertIn('gross_dividends', result)
            self.assertIn('calculated_tax', result)
            self.assertEqual(result['gross_dividends'], expected_dividends)
            self.assertEqual(result['calculated_tax'], expected_tax)
            self.assertEqual(result['net_yield'], expected_net_yield)

    def test_sync_portfolio_aggregate_stream_flow(self):
        portfolio_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        random_stream_data = io.BytesIO(uuid.uuid4().bytes + b'random_payload_stream')

        aggregated_dividends = {
            'total_amount': round(random.uniform(500.0, 15000.0), 2),
            'currency': random.choice(['USD', 'EUR', 'RUB'])
        }

        tax_calculation_result = {
            'tax_due': round(random.uniform(50.0, 1500.0), 2),
            'status': 'calculated'
        }

        with patch('skills.market_portfolio_dividend_tracker.DividendTracker.aggregate_portfolio_dividends', return_value=aggregated_dividends) as mock_agg_div, \
             patch('skills.market_portfolio_tax_calculator.MarketPortfolioTaxCalculator.process_dividend_stream', return_value=tax_calculation_result) as mock_proc_stream:

            sync_result = self.sync_engine.synchronize_portfolio_audit_flow(
                portfolio_id=portfolio_id,
                user_id=user_id,
                stream_source=random_stream_data
            )

            mock_agg_div.assert_called_once_with(portfolio_id)
            mock_proc_stream.assert_called_once()

            self.assertEqual(sync_result['portfolio_id'], portfolio_id)
            self.assertEqual(sync_result['dividends'], aggregated_dividends)
            self.assertEqual(sync_result['tax_report'], tax_calculation_result)

    def test_sync_raises_exception_on_tracker_failure(self):
        portfolio_id = str(uuid.uuid4())
        asset_ticker = ''.join(random.choices(string.ascii_uppercase, k=4))
        shares_count = random.randint(1, 100)
        tax_rate = 0.13

        error_message = f"Critical sync failure: {uuid.uuid4().hex}"

        with patch('skills.market_portfolio_dividend_tracker.DividendTracker.calculate_projected_dividends', side_effect=Exception(error_message)) as mock_div_calc:

            with self.assertRaises(TaxDividendSyncException) as ctx:
                self.sync_engine.calculate_synchronized_net_yield(
                    portfolio_id=portfolio_id,
                    asset_ticker=asset_ticker,
                    shares_count=shares_count,
                    tax_rate=tax_rate
                )

            mock_div_calc.assert_called_once()
            self.assertIn(error_message, str(ctx.exception))


if __name__ == '__main__':
    unittest.main()