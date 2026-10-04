import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import io

from skills.market_portfolio_yield_evaluator import (
    MarketPortfolioYieldEvaluator,
    calculate_net_yield,
    evaluate_portfolio_yield,
)


class TestMarketPortfolioYieldEvaluator(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.portfolio_value = round(random.uniform(1000.0, 1000000.0), 2)
        self.gross_dividends = round(random.uniform(50.0, 5000.0), 2)
        self.tax_amount = round(random.uniform(5.0, 500.0), 2)
        self.effective_rate = round(self.tax_amount / self.gross_dividends, 4)
        self.currency = random.choice(["USD", "EUR", "GBP", "RUB"])
        self.ticker = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=random.randint(3, 5)))
        self.shares_count = random.randint(10, 1000)
        self.tax_rate = round(random.uniform(0.05, 0.3), 2)

    def test_calculate_net_dividend_yield_success(self):
        mock_dt = MagicMock()
        mock_dt.aggregate_portfolio_dividends.return_value = {
            "total_dividends": self.gross_dividends,
            "currency": self.currency,
        }

        mock_tc = MagicMock()
        mock_tc.calculate_tax.return_value = {
            "tax_amount": self.tax_amount,
            "effective_rate": self.effective_rate,
        }

        evaluator = MarketPortfolioYieldEvaluator(dividend_tracker=mock_dt, tax_calculator=mock_tc)
        result = evaluator.calculate_net_dividend_yield(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.portfolio_value,
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["portfolio_value"], self.portfolio_value)
        self.assertEqual(result["gross_dividends"], self.gross_dividends)
        self.assertEqual(result["tax_amount"], self.tax_amount)
        self.assertEqual(result["currency"], self.currency)
        self.assertAlmostEqual(result["net_dividends"], self.gross_dividends - self.tax_amount)

        expected_yield = ((self.gross_dividends - self.tax_amount) / self.portfolio_value) * 100.0
        self.assertAlmostEqual(result["net_dividend_yield"], expected_yield)
        mock_dt.aggregate_portfolio_dividends.assert_called_once_with(self.portfolio_id)
        mock_tc.calculate_tax.assert_called_once_with(
            portfolio_id=self.portfolio_id, gross_dividends=self.gross_dividends
        )

    def test_calculate_net_dividend_yield_with_primitive_returns(self):
        mock_dt = MagicMock()
        mock_dt.aggregate_portfolio_dividends.return_value = self.gross_dividends

        mock_tc = MagicMock()
        mock_tc.calculate_tax.return_value = self.tax_amount

        evaluator = MarketPortfolioYieldEvaluator(dividend_tracker=mock_dt, tax_calculator=mock_tc)
        result = evaluator.calculate_net_dividend_yield(
            portfolio_id=self.portfolio_id,
            total_portfolio_value=self.portfolio_value,
        )

        self.assertEqual(result["gross_dividends"], self.gross_dividends)
        self.assertEqual(result["tax_amount"], self.tax_amount)
        self.assertEqual(result["currency"], "USD")
        self.assertAlmostEqual(result["net_dividends"], self.gross_dividends - self.tax_amount)

    def test_evaluate_portfolio_yield_aliases(self):
        mock_dt = MagicMock()
        mock_dt.aggregate_portfolio_dividends.return_value = self.gross_dividends
        mock_tc = MagicMock()
        mock_tc.calculate_tax.return_value = self.tax_amount

        evaluator = MarketPortfolioYieldEvaluator(dividend_tracker=mock_dt, tax_calculator=mock_tc)

        res1 = evaluator.evaluate_portfolio_yield(self.portfolio_id, portfolio_value=self.portfolio_value)
        res2 = evaluator.calculate_net_yield(self.portfolio_id, total_portfolio_value=self.portfolio_value)
        res3 = evaluator.evaluate_net_dividend_yield(self.portfolio_id, portfolio_value=self.portfolio_value)
        res4 = evaluator.evaluate_yield(self.portfolio_id, portfolio_value=self.portfolio_value)

        for r in [res1, res2, res3, res4]:
            self.assertEqual(r["portfolio_id"], self.portfolio_id)
            self.assertEqual(r["gross_dividends"], self.gross_dividends)

    def test_process_yield_stream_with_calculator_method(self):
        mock_tc = MagicMock()
        expected_output = "".join(random.choices("abcdef", k=10))
        mock_tc.process_dividend_stream.return_value = expected_output

        evaluator = MarketPortfolioYieldEvaluator(tax_calculator=mock_tc)
        stream_data = io.BytesIO(b"random_bytes")

        res = evaluator.process_yield_stream(stream_data)
        self.assertEqual(res, expected_output)
        mock_tc.process_dividend_stream.assert_called_once_with(stream_data)

    def test_process_yield_stream_fallback(self):
        mock_tc = MagicMock(spec=[])
        evaluator = MarketPortfolioYieldEvaluator(tax_calculator=mock_tc)
        random_bytes = b"some_random_stream_content_" + uuid.uuid4().hex.encode()
        stream_data = io.BytesIO(random_bytes)

        res = evaluator.process_yield_stream(stream_data)
        self.assertEqual(res, random_bytes)

    def eval_projected_yield_test(self):
        mock_dt = MagicMock()
        expected_projected = round(random.uniform(10.0, 500.0), 2)
        mock_dt.calculate_projected_dividends.return_value = expected_projected

        evaluator = MarketPortfolioYieldEvaluator(dividend_tracker=mock_dt)
        res = evaluator.evaluate_projected_yield(self.ticker, self.shares_count, self.portfolio_value, self.tax_rate)

        self.assertEqual(res, expected_projected)
        mock_dt.calculate_projected_dividends.assert_called_once_with(
            self.ticker, self.shares_count, self.tax_rate
        )

    def test_module_level_helpers(self):
        with patch("skills.market_portfolio_yield_evaluator.MarketPortfolioYieldEvaluator") as mock_eval_cls:
            instance = mock_eval_cls.return_value
            expected_dict = {"portfolio_id": self.portfolio_id}
            instance.calculate_net_dividend_yield.return_value = expected_dict

            res1 = calculate_net_yield(self.portfolio_id, total_portfolio_value=self.portfolio_value)
            self.assertEqual(res1, expected_dict)

            res2 = evaluate_portfolio_yield(self.portfolio_id, portfolio_value=self.portfolio_value)
            self.assertEqual(res2, expected_dict)

    def test_yield_evaluation_with_patching_internal_dependencies(self):
        with patch("skills.market_portfolio_yield_evaluator.DividendTracker") as mock_dt_cls, \
             patch("skills.market_portfolio_yield_evaluator.MarketPortfolioTaxCalculator") as mock_tc_cls:

            instance_dt = mock_dt_cls.return_value
            instance_dt.aggregate_portfolio_dividends.return_value = self.gross_dividends

            instance_tc = mock_tc_cls.return_value
            instance_tc.calculate_tax.return_value = self.tax_amount

            evaluator = MarketPortfolioYieldEvaluator()
            res = evaluator.calculate_net_dividend_yield(
                portfolio_id=self.portfolio_id,
                total_portfolio_value=self.portfolio_value
            )

            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            self.assertEqual(res["gross_dividends"], self.gross_dividends)
            self.assertEqual(res["tax_amount"], self.tax_amount)
            instance_dt.aggregate_portfolio_dividends.assert_called_once()
            instance_tc.calculate_tax.assert_called_once()