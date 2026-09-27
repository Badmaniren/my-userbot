import unittest
from unittest.mock import patch, MagicMock
import uuid
import random

from skills.market_portfolio_tax_dividend_unifier import (
    TaxDividendUnifier,
    TaxDividendUnifierException,
    unify_portfolio_yield,
    unifier_pipeline
)


class TestTaxDividendUnifier(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.user_id = uuid.uuid4().hex
        self.asset_ticker = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5))
        self.shares_count = random.randint(1, 1000)
        self.tax_rate = round(random.uniform(0.05, 0.25), 2)

        self.mock_tax_calculator = MagicMock()
        self.mock_dividend_tracker = MagicMock()

    def test_calculate_net_yield_success(self):
        total_tax = round(random.uniform(10.0, 500.0), 2)
        total_dividends = round(total_tax + random.uniform(50.0, 1000.0), 2)
        expected_net = round(total_dividends - total_tax, 2)

        self.mock_tax_calculator.calculate_tax.return_value = {"total_tax": total_tax}
        self.mock_dividend_tracker.aggregate_portfolio_dividends.return_value = {"total_dividends": total_dividends}

        unifier = TaxDividendUnifier(
            tax_calculator=self.mock_tax_calculator,
            dividend_tracker=self.mock_dividend_tracker
        )

        result = unifier.calculate_net_yield(self.portfolio_id)

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["tax_withheld"], total_tax)
        self.assertEqual(result["gross_dividends"], total_dividends)
        self.assertEqual(result["net_yield"], expected_net)

        self.mock_tax_calculator.calculate_tax.assert_called_once_with(self.portfolio_id)
        self.mock_dividend_tracker.aggregate_portfolio_dividends.assert_called_once_with(self.portfolio_id)

    def test_calculate_net_yield_exception_handling(self):
        error_msg = f"db_error_{uuid.uuid4().hex}"
        self.mock_tax_calculator.calculate_tax.side_effect = Exception(error_msg)

        unifier = TaxDividendUnifier(
            tax_calculator=self.mock_tax_calculator,
            dividend_tracker=self.mock_dividend_tracker
        )

        with self.assertRaises(TaxDividendUnifierException) as ctx:
            unifier.calculate_net_yield(self.portfolio_id)

        self.assertIn(error_msg, str(ctx.exception))

    def test_calculate_net_yield_custom_unifier_exception(self):
        custom_error = TaxDividendUnifierException(f"custom_{uuid.uuid4().hex}")
        self.mock_tax_calculator.calculate_tax.side_effect = custom_error

        unifier = TaxDividendUnifier(
            tax_calculator=self.mock_tax_calculator,
            dividend_tracker=self.mock_dividend_tracker
        )

        with self.assertRaises(TaxDividendUnifierException) as ctx:
            unifier.calculate_net_yield(self.portfolio_id)

        self.assertEqual(ctx.exception, custom_error)

    def test_process_stream_data_with_process_dividend_stream(self):
        stream_data = {"event_id": uuid.uuid4().hex, "amount": random.uniform(1.0, 100.0)}

        delattr(self.mock_dividend_tracker, "process_dividends")
        self.mock_dividend_tracker.process_dividend_stream = MagicMock()

        unifier = TaxDividendUnifier(
            tax_calculator=self.mock_tax_calculator,
            dividend_tracker=self.mock_dividend_tracker
        )

        res = unifier.process_stream_data(stream_data)
        self.assertTrue(res)
        self.mock_tax_calculator.process_dividend_stream.assert_called_once_with(stream_data)
        self.mock_dividend_tracker.process_dividend_stream.assert_called_once_with(stream_data)

    def test_process_stream_data_with_process_dividends(self):
        stream_data = {"event_id": uuid.uuid4().hex, "amount": random.uniform(1.0, 100.0)}

        self.mock_dividend_tracker.process_dividends = MagicMock()
        if hasattr(self.mock_dividend_tracker, "process_dividend_stream"):
            del self.mock_dividend_tracker.process_dividend_stream

        unifier = TaxDividendUnifier(
            tax_calculator=self.mock_tax_calculator,
            dividend_tracker=self.mock_dividend_tracker
        )

        res = unifier.process_stream_data(stream_data)
        self.assertTrue(res)
        self.mock_tax_calculator.process_dividend_stream.assert_called_once_with(stream_data)
        self.mock_dividend_tracker.process_dividends.assert_called_once_with(stream_data)

    def test_unify_portfolio_yield_function(self):
        total_tax = round(random.uniform(5.0, 50.0), 2)
        total_dividends = round(total_tax + random.uniform(10.0, 100.0), 2)
        expected_net = round(total_dividends - total_tax, 2)

        with patch('skills.market_portfolio_tax_dividend_unifier.MarketPortfolioTaxCalculator') as MockTaxCalc, \
             patch('skills.market_portfolio_tax_dividend_unifier.DividendTracker') as MockDivTrack:

            instance_tax = MockTaxCalc.return_value
            instance_tax.calculate_tax.return_value = {"total_tax": total_tax}

            instance_div = MockDivTrack.return_value
            instance_div.aggregate_portfolio_dividends.return_value = {"total_dividends": total_dividends}

            result = unify_portfolio_yield(self.portfolio_id, self.user_id)

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["tax_withheld"], total_tax)
            self.assertEqual(result["gross_dividends"], total_dividends)
            self.assertEqual(result["net_yield"], expected_net)

    def test_unifier_pipeline_function(self):
        dividend_stream = [
            {"amount": round(random.uniform(10.0, 100.0), 2)},
            {"amount": round(random.uniform(20.0, 200.0), 2)}
        ]
        sum_div = sum(item["amount"] for item in dividend_stream)
        expected_tax = round(sum_div * self.tax_rate, 2)
        expected_net = round(sum_div - expected_tax, 2)

        with patch('skills.market_portfolio_tax_dividend_unifier.MarketPortfolioTaxCalculator'), \
             patch('skills.market_portfolio_tax_dividend_unifier.DividendTracker'):

            result = unifier_pipeline(
                portfolio_id=self.portfolio_id,
                user_id=self.user_id,
                asset_ticker=self.asset_ticker,
                shares_count=self.shares_count,
                tax_rate=self.tax_rate,
                dividend_stream=dividend_stream
            )

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["user_id"], self.user_id)
            self.assertEqual(result["asset_ticker"], self.asset_ticker)
            self.assertEqual(result["shares_count"], self.shares_count)
            self.assertEqual(result["tax_rate"], self.tax_rate)
            self.assertEqual(result["dividend_stream"], dividend_stream)
            self.assertEqual(result["total_dividends"], sum_div)
            self.assertEqual(result["total_tax"], expected_tax)
            self.assertEqual(result["net_yield"], expected_net)