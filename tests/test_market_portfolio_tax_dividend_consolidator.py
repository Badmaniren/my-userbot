import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.market_portfolio_tax_dividend_consolidator import (
    TaxDividendConsolidator,
    ConsolidatorException,
    consolidate_portfolio_finances
)


class TestMarketPortfolioTaxDividendConsolidator(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        self.db_storage = MagicMock()
        self.consolidator = TaxDividendConsolidator(db_storage=self.db_storage)

    def test_consolidator_initialization_and_composition(self):
        rand_db = MagicMock()
        with patch('skills.market_portfolio_tax_dividend_consolidator.MarketPortfolioTaxCalculator') as mock_tax_calc, \
             patch('skills.market_portfolio_tax_dividend_consolidator.DividendTracker') as mock_div_track:

            instance = TaxDividendConsolidator(db_storage=rand_db)
            self.assertEqual(instance.db_storage, rand_db)
            mock_tax_calc.assert_called_once()
            mock_div_track.assert_called_once()

    def test_consolidate_finances_success(self):
        random_tax_amount = round(random.uniform(100.0, 50000.0), 2)
        random_div_amount = round(random.uniform(500.0, 100000.0), 2)
        random_net_yield = round(random_div_amount - random_tax_amount, 2)
        random_currency = random.choice(['USD', 'EUR', 'RUB', 'GBP'])

        mock_tax_result = {
            'portfolio_id': self.portfolio_id,
            'total_tax': random_tax_amount,
            'currency': random_currency
        }

        mock_div_result = {
            'portfolio_id': self.portfolio_id,
            'total_dividends': random_div_amount,
            'currency': random_currency
        }

        with patch.object(self.consolidator.tax_calculator, 'calculate_tax', return_value=mock_tax_result) as mock_tax, \
             patch.object(self.consolidator.dividend_tracker, 'aggregate_portfolio_dividends', return_value=mock_div_result) as mock_div:

            report = self.consolidator.consolidate(self.portfolio_id)

            mock_tax.assert_called_once_with(self.portfolio_id)
            mock_div.assert_called_once_with(self.portfolio_id)

            self.assertEqual(report['portfolio_id'], self.portfolio_id)
            self.assertEqual(report['tax_details'], mock_tax_result)
            self.assertEqual(report['dividend_details'], mock_div_result)
            self.assertEqual(report['net_financial_result'], random_net_yield)
            self.assertEqual(report['currency'], random_currency)
            self.assertIn('consolidated_at', report)

    def test_consolidate_finances_currency_mismatch_raises_exception(self):
        mock_tax_result = {
            'portfolio_id': self.portfolio_id,
            'total_tax': random.uniform(10.0, 500.0),
            'currency': 'USD'
        }

        mock_div_result = {
            'portfolio_id': self.portfolio_id,
            'total_dividends': random.uniform(100.0, 1000.0),
            'currency': 'EUR'
        }

        with patch.object(self.consolidator.tax_calculator, 'calculate_tax', return_value=mock_tax_result), \
             patch.object(self.consolidator.dividend_tracker, 'aggregate_portfolio_dividends', return_value=mock_div_result):

            with self.assertRaises(ConsolidatorException) as ctx:
                self.consolidator.consolidate(self.portfolio_id)

            self.assertIn('Currency mismatch', str(ctx.exception))

    def test_functional_consolidate_portfolio_finances_wrapper(self):
        random_portfolio = str(uuid.uuid4())
        expected_report = {
            'portfolio_id': random_portfolio,
            'net_financial_result': round(random.uniform(1000.0, 9999.0), 2),
            'currency': 'USD'
        }

        with patch('skills.market_portfolio_tax_dividend_consolidator.TaxDividendConsolidator') as MockConsolidatorClass:
            mock_instance = MockConsolidatorClass.return_value
            mock_instance.consolidate.return_value = expected_report

            result = consolidate_portfolio_finances(random_portfolio)

            MockConsolidatorClass.assert_called_once()
            mock_instance.consolidate.assert_called_once_with(random_portfolio)
            self.assertEqual(result, expected_report)

    def test_consolidator_exception_handling_on_tax_failure(self):
        random_error_msg = ''.join(random.choices(string.ascii_letters + string.digits, k=15))

        with patch.object(self.consolidator.tax_calculator, 'calculate_tax', side_effect=Exception(random_error_msg)):
            with self.assertRaises(ConsolidatorException) as ctx:
                self.consolidator.consolidate(self.portfolio_id)

            self.assertIn(random_error_msg, str(ctx.exception))

    def test_consolidator_exception_handling_on_dividend_failure(self):
        random_error_msg = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
        mock_tax_result = {'portfolio_id': self.portfolio_id, 'total_tax': 100.0, 'currency': 'RUB'}

        with patch.object(self.consolidator.tax_calculator, 'calculate_tax', return_value=mock_tax_result), \
             patch.object(self.consolidator.dividend_tracker, 'aggregate_portfolio_dividends', side_effect=Exception(random_error_msg)):

            with self.assertRaises(ConsolidatorException) as ctx:
                self.consolidator.consolidate(self.portfolio_id)

            self.assertIn(random_error_msg, str(ctx.exception))


if __name__ == '__main__':
    unittest.main()