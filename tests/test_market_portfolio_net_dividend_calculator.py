import io
import random
import string
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.market_portfolio_dividend_tracker import DividendTrackerException
from skills.market_portfolio_net_dividend_calculator import (
    NetDividendCalculator,
    NetDividendCalculatorException,
)


class TestMarketPortfolioNetDividendCalculator(unittest.TestCase):
    def _random_str(self, length=8):
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def _random_float(self, min_val=10.0, max_val=1000.0):
        return round(random.uniform(min_val, max_val), 4)

    def _random_int(self, min_val=1, max_val=500):
        return random.randint(min_val, max_val)

    def test_init_default_dependencies(self):
        storage_mock = MagicMock()
        gateway_mock = MagicMock()

        with patch("skills.market_portfolio_net_dividend_calculator.DividendTracker") as mock_tracker_cls, \
             patch("skills.market_portfolio_net_dividend_calculator.MarketPortfolioTaxCalculator") as mock_tax_cls:
            tracker_instance = MagicMock()
            tax_instance = MagicMock()
            mock_tracker_cls.return_value = tracker_instance
            mock_tax_cls.return_value = tax_instance

            calc = NetDividendCalculator(
                db_storage=storage_mock,
                api_gateway=gateway_mock
            )

            self.assertIs(calc.db_storage, storage_mock)
            self.assertIs(calc.api_gateway, gateway_mock)
            self.assertIs(calc.dividend_tracker, tracker_instance)
            self.assertIs(calc.tax_calculator, tax_instance)
            mock_tax_cls.assert_called_once_with()
            mock_tracker_cls.assert_called_once_with(
                db_storage=storage_mock,
                tax_calculator=None,
                api_gateway=gateway_mock
            )

    def test_init_injected_dependencies(self):
        storage_mock = MagicMock()
        gateway_mock = MagicMock()
        tracker_mock = MagicMock()
        tax_mock = MagicMock()

        calc = NetDividendCalculator(
            db_storage=storage_mock,
            dividend_tracker=tracker_mock,
            tax_calculator=tax_mock,
            api_gateway=gateway_mock
        )

        self.assertIs(calc.dividend_tracker, tracker_mock)
        self.assertIs(calc.tax_calculator, tax_mock)
        self.assertIs(calc.db_storage, storage_mock)
        self.assertIs(calc.api_gateway, gateway_mock)

    def test_calculate_net_dividend_yield_success_with_asset_price(self):
        tracker_mock = MagicMock()
        tax_mock = MagicMock()
        calc = NetDividendCalculator(dividend_tracker=tracker_mock, tax_calculator=tax_mock)

        portfolio_id = str(uuid.uuid4())
        asset_ticker = f"TICKER_{self._random_str(4).upper()}"
        shares_count = self._random_int(10, 200)
        asset_price = self._random_float(50.0, 500.0)
        tax_rate = round(random.uniform(0.05, 0.35), 2)

        gross_dividend = self._random_float(100.0, 1000.0)
        returned_ticker = f"{asset_ticker}_MODIFIED_{self._random_str(3)}"
        returned_shares = shares_count

        tracker_mock.calculate_projected_dividends.return_value = {
            'ticker': returned_ticker,
            'shares': returned_shares,
            'gross_dividend': gross_dividend
        }

        tax_amount = round(gross_dividend * tax_rate, 4)
        tax_mock.calculate_tax.return_value = {
            'tax_amount': tax_amount
        }

        result = calc.calculate_net_dividend_yield(
            portfolio_id=portfolio_id,
            asset_ticker=asset_ticker,
            shares_count=shares_count,
            asset_price=asset_price,
            tax_rate=tax_rate
        )

        tracker_mock.calculate_projected_dividends.assert_called_once_with(
            asset_ticker=asset_ticker,
            shares_count=shares_count,
            tax_rate=tax_rate
        )
        tax_mock.calculate_tax.assert_called_once_with(
            portfolio_id=portfolio_id,
            gross_amount=gross_dividend
        )

        expected_net_dividend = gross_dividend - tax_amount
        expected_yield = expected_net_dividend / (shares_count * asset_price)

        self.assertEqual(result['ticker'], returned_ticker)
        self.assertEqual(result['shares'], returned_shares)
        self.assertAlmostEqual(result['net_dividend_amount'], expected_net_dividend, places=4)
        self.assertAlmostEqual(result['net_dividend_yield'], expected_yield, places=4)

    def test_calculate_net_dividend_yield_zero_price_or_shares(self):
        tracker_mock = MagicMock()
        tax_mock = MagicMock()
        calc = NetDividendCalculator(dividend_tracker=tracker_mock, tax_calculator=tax_mock)

        portfolio_id = str(uuid.uuid4())
        asset_ticker = f"TICK_{self._random_str(3)}"
        gross_dividend = self._random_float(50.0, 300.0)
        tax_amount = self._random_float(5.0, 30.0)

        tracker_mock.calculate_projected_dividends.return_value = {
            'ticker': asset_ticker,
            'gross_dividend': gross_dividend
        }
        tax_mock.calculate_tax.return_value = {
            'tax_amount': tax_amount
        }

        result_no_price = calc.calculate_net_dividend_yield(
            portfolio_id=portfolio_id,
            asset_ticker=asset_ticker,
            shares_count=10,
            asset_price=None
        )
        self.assertEqual(result_no_price['net_dividend_yield'], 0.0)

        result_zero_shares = calc.calculate_net_dividend_yield(
            portfolio_id=portfolio_id,
            asset_ticker=asset_ticker,
            shares_count=0,
            asset_price=100.0
        )
        self.assertEqual(result_zero_shares['net_dividend_yield'], 0.0)

        result_negative_price = calc.calculate_net_dividend_yield(
            portfolio_id=portfolio_id,
            asset_ticker=asset_ticker,
            shares_count=10,
            asset_price=-50.0
        )
        self.assertEqual(result_negative_price['net_dividend_yield'], 0.0)

    def test_calculate_net_dividend_yield_tracker_exception(self):
        tracker_mock = MagicMock()
        calc = NetDividendCalculator(dividend_tracker=tracker_mock, tax_calculator=MagicMock())

        err_msg = f"Tracker failed: {self._random_str(10)}"
        tracker_mock.calculate_projected_dividends.side_effect = DividendTrackerException(err_msg)

        with self.assertRaises(NetDividendCalculatorException) as ctx:
            calc.calculate_net_dividend_yield(
                portfolio_id=str(uuid.uuid4()),
                asset_ticker=self._random_str(5),
                shares_count=self._random_int(1, 100)
            )
        self.assertIn(err_msg, str(ctx.exception))

    def test_calculate_net_dividend_yield_unexpected_exception(self):
        tracker_mock = MagicMock()
        calc = NetDividendCalculator(dividend_tracker=tracker_mock, tax_calculator=MagicMock())

        err_msg = f"Unexpected failure {self._random_str(12)}"
        tracker_mock.calculate_projected_dividends.side_effect = RuntimeError(err_msg)

        with self.assertRaises(NetDividendCalculatorException) as ctx:
            calc.calculate_net_dividend_yield(
                portfolio_id=str(uuid.uuid4()),
                asset_ticker=self._random_str(5),
                shares_count=self._random_int(1, 100)
            )
        self.assertIn(err_msg, str(ctx.exception))

    def test_aggregate_net_dividends_for_portfolio_success(self):
        tracker_mock = MagicMock()
        tax_mock = MagicMock()
        calc = NetDividendCalculator(dividend_tracker=tracker_mock, tax_calculator=tax_mock)

        portfolio_id = f"port_{uuid.uuid4().hex}"
        random_count = random.randint(2, 5)
        mock_dividends = [
            {'asset': self._random_str(4), 'amount': self._random_float(10.0, 100.0)}
            for _ in range(random_count)
        ]
        total_net_val = sum(item['amount'] for item in mock_dividends) * 0.87

        tracker_mock.aggregate_portfolio_dividends.return_value = mock_dividends
        tax_mock.process_dividend_stream.return_value = {
            'total_net': total_net_val,
            'processed_count': random_count
        }

        result = calc.aggregate_net_dividends_for_portfolio(portfolio_id)

        tracker_mock.aggregate_portfolio_dividends.assert_called_once_with(portfolio_id)
        tax_mock.process_dividend_stream.assert_called_once_with(mock_dividends)

        self.assertEqual(result['portfolio_id'], portfolio_id)
        self.assertEqual(result['total_net_dividends'], total_net_val)

    def test_aggregate_net_dividends_for_portfolio_exception(self):
        tracker_mock = MagicMock()
        calc = NetDividendCalculator(dividend_tracker=tracker_mock, tax_calculator=MagicMock())

        portfolio_id = f"port_{uuid.uuid4().hex}"
        err_msg = f"Failed to aggregate stream: {self._random_str(15)}"
        tracker_mock.aggregate_portfolio_dividends.side_effect = ValueError(err_msg)

        with self.assertRaises(NetDividendCalculatorException) as ctx:
            calc.aggregate_net_dividends_for_portfolio(portfolio_id)
        self.assertIn(err_msg, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()