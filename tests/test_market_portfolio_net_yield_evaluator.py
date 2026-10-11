import unittest
from unittest.mock import patch
import random
import uuid

from skills.market_portfolio_net_yield_evaluator import (
    NetYieldEvaluator,
    evaluate_net_yield
)


class TestMarketPortfolioNetYieldEvaluator(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.json"
        self.portfolio_url = f"file:///{uuid.uuid4().hex}.json"
        self.portfolio_id = uuid.uuid4().hex
        self.stream_id = uuid.uuid4().hex

        self.total_value = round(random.uniform(1000.0, 50000.0), 2)
        self.unrealized_pnl = round(random.uniform(-500.0, 2500.0), 2)
        self.realized_pnl = round(random.uniform(-200.0, 1500.0), 2)
        self.total_tax = round(random.uniform(50.0, 500.0), 2)

    def test_evaluate_net_yield_basic(self):
        evaluator = NetYieldEvaluator(storage_file=self.storage_file)

        mock_valuation_data = {
            "total_value": self.total_value,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl
        }
        mock_tax_data = {
            "total_tax": self.total_tax
        }

        with patch.object(evaluator.valuation_engine, 'evaluate_portfolio', return_value=mock_valuation_data) as mock_eval, \
             patch.object(evaluator.tax_calculator, 'calculate_tax', return_value=mock_tax_data) as mock_tax:

            result = evaluator.evaluate_net_yield(self.portfolio_url)

            mock_eval.assert_called_once_with(self.portfolio_url)
            mock_tax.assert_called_once()

            expected_net_value = self.total_value - self.total_tax
            expected_yield = round(
                ((self.unrealized_pnl + self.realized_pnl - self.total_tax) / self.total_value) * 100, 4
            )

            self.assertAlmostEqual(result["net_portfolio_value"], expected_net_value)
            self.assertAlmostEqual(result["net_yield_percentage"], expected_yield)

    def test_evaluate_net_yield_zero_value(self):
        evaluator = NetYieldEvaluator(storage_file=self.storage_file)

        mock_valuation_data = {
            "total_value": 0.0,
            "unrealized_pnl": 0.0,
            "realized_pnl": 0.0
        }
        mock_tax_data = {
            "total_tax": 0.0
        }

        with patch.object(evaluator.valuation_engine, 'evaluate_portfolio', return_value=mock_valuation_data), \
             patch.object(evaluator.tax_calculator, 'calculate_tax', return_value=mock_tax_data):

            result = evaluator.evaluate_net_yield(self.portfolio_url)

            self.assertEqual(result["net_portfolio_value"], 0.0)
            self.assertEqual(result["net_yield_percentage"], 0.0)

    def test_evaluate_net_yield_with_stream_integration(self):
        evaluator = NetYieldEvaluator(storage_file=self.storage_file)

        mock_valuation_data = {
            "total_value": self.total_value,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl
        }
        mock_stream_result = {
            "dividend_processed": True,
            "stream_id": self.stream_id,
            "amount": round(random.uniform(10.0, 100.0), 2)
        }
        mock_tax_data = {
            "total_tax": self.total_tax
        }

        with patch.object(evaluator.valuation_engine, 'evaluate_portfolio', return_value=mock_valuation_data), \
             patch.object(evaluator.tax_calculator, 'process_dividend_stream', return_value=mock_stream_result) as mock_stream, \
             patch.object(evaluator.tax_calculator, 'calculate_tax', return_value=mock_tax_data):

            stream_input = {"id": self.stream_id}
            result = evaluator.evaluate_net_yield_with_stream(self.portfolio_url, stream_input)

            mock_stream.assert_called_once_with(stream_input)

            self.assertIn("dividend_processed", result)
            self.assertEqual(result["stream_id"], self.stream_id)
            self.assertIn("net_portfolio_value", result)
            self.assertIn("net_yield_percentage", result)

    def test_module_level_evaluate_net_yield(self):
        mock_valuation_data = {
            "total_value": self.total_value,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl
        }
        mock_tax_data = {
            "total_tax": self.total_tax
        }

        with patch('skills.market_portfolio_net_yield_evaluator.PortfolioValuation.evaluate_portfolio', return_value=mock_valuation_data), \
             patch('skills.market_portfolio_net_yield_evaluator.MarketPortfolioTaxCalculator.calculate_tax', return_value=mock_tax_data):

            result = evaluate_net_yield(self.portfolio_id, self.portfolio_url)

            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            expected_net_yield = self.total_value - self.total_tax
            self.assertAlmostEqual(result["net_yield"], expected_net_yield)