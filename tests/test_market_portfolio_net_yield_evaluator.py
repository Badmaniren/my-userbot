import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_net_yield_evaluator import NetYieldEvaluator

class TestNetYieldEvaluator(unittest.TestCase):

    def setUp(self):
        self.random_prefix = uuid.uuid4().hex[:8]
        self.portfolio_url = f"https://api.market.portfolio/{uuid.uuid4().hex}.json"
        self.storage_path = f"/tmp/storage_{uuid.uuid4().hex}.db"
        self.user_id = str(random.randint(10000, 99999))
        self.holding_period = random.randint(30, 1460)
        
        self.total_value = round(random.uniform(10000.0, 1000000.0), 2)
        self.unrealized_pnl = round(random.uniform(-50000.0, 150000.0), 2)
        self.realized_pnl = round(random.uniform(-20000.0, 80000.0), 2)
        
        self.unrealized_tax = round(abs(self.unrealized_pnl) * 0.13, 2) if self.unrealized_pnl > 0 else 0.0
        self.realized_tax = round(abs(self.realized_pnl) * 0.13, 2) if self.realized_pnl > 0 else 0.0
        self.total_tax = round(self.unrealized_tax + self.realized_tax, 2)

    def test_evaluate_net_yield_composition_and_math(self):
        with patch('skills.market_portfolio_net_yield_evaluator.PortfolioValuation') as mock_valuation_cls, \
             patch('skills.market_portfolio_net_yield_evaluator.MarketPortfolioTaxCalculator') as mock_tax_calc_cls:

            mock_valuation_instance = mock_valuation_cls.return_value
            mock_valuation_instance.evaluate_portfolio.return_value = {
                "total_value": self.total_value,
                "unrealized_pnl": self.unrealized_pnl,
                "realized_pnl": self.realized_pnl
            }

            mock_tax_instance = mock_tax_calc_cls.return_value
            mock_tax_instance.calculate_tax.return_value = {
                "unrealized_tax": self.unrealized_tax,
                "realized_tax": self.realized_tax,
                "total_tax": self.total_tax
            }

            evaluator = NetYieldEvaluator(storage_file=self.storage_path)
            result = evaluator.evaluate_net_yield(self.portfolio_url)

            mock_valuation_cls.assert_called_once_with(self.storage_path)
            mock_valuation_instance.evaluate_portfolio.assert_called_once_with(self.portfolio_url)
            
            mock_tax_calc_cls.assert_called_once()
            mock_tax_instance.calculate_tax.assert_called_once()

            expected_net_value = self.total_value - self.total_tax
            expected_net_yield_percentage = round(((self.unrealized_pnl + self.realized_pnl - self.total_tax) / self.total_value) * 100, 4)

            self.assertIn("net_portfolio_value", result)
            self.assertIn("net_yield_percentage", result)
            self.assertEqual(result["net_portfolio_value"], expected_net_value)
            self.assertEqual(result["net_yield_percentage"], expected_net_yield_percentage)

    def test_evaluate_net_yield_zero_division_guard(self):
        with patch('skills.market_portfolio_net_yield_evaluator.PortfolioValuation') as mock_valuation_cls, \
             patch('skills.market_portfolio_net_yield_evaluator.MarketPortfolioTaxCalculator') as mock_tax_calc_cls:

            mock_valuation_instance = mock_valuation_cls.return_value
            mock_valuation_instance.evaluate_portfolio.return_value = {
                "total_value": 0.0,
                "unrealized_pnl": 0.0,
                "realized_pnl": 0.0
            }

            mock_tax_instance = mock_tax_calc_cls.return_value
            mock_tax_instance.calculate_tax.return_value = {
                "unrealized_tax": 0.0,
                "realized_tax": 0.0,
                "total_tax": 0.0
            }

            evaluator = NetYieldEvaluator(storage_file=self.storage_path)
            result = evaluator.evaluate_net_yield(self.portfolio_url)

            self.assertEqual(result["net_portfolio_value"], 0.0)
            self.assertEqual(result["net_yield_percentage"], 0.0)

    def test_evaluate_net_yield_with_stream_io_mock(self):
        random_stream_data = ''.join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        mock_stream = io.BytesIO(random_stream_data)

        with patch('skills.market_portfolio_net_yield_evaluator.PortfolioValuation') as mock_valuation_cls, \
             patch('skills.market_portfolio_net_yield_evaluator.MarketPortfolioTaxCalculator') as mock_tax_calc_cls:

            mock_valuation_instance = mock_valuation_cls.return_value
            mock_valuation_instance.evaluate_portfolio.return_value = {
                "total_value": self.total_value,
                "unrealized_pnl": self.unrealized_pnl,
                "realized_pnl": self.realized_pnl
            }

            mock_tax_instance = mock_tax_calc_cls.return_value
            mock_tax_instance.process_dividend_stream.return_value = {
                "stream_processed": True,
                "data_snippet": mock_stream.read().decode('utf-8')
            }
            mock_tax_instance.calculate_tax.return_value = {
                "unrealized_tax": self.unrealized_tax,
                "realized_tax": self.realized_tax,
                "total_tax": self.total_tax
            }

            evaluator = NetYieldEvaluator(storage_file=self.storage_path)
            result = evaluator.evaluate_net_yield_with_stream(self.portfolio_url, mock_stream)

            mock_tax_instance.process_dividend_stream.assert_called_once()
            self.assertTrue(result["stream_processed"])
            self.assertEqual(result["data_snippet"], random_stream_data.decode('utf-8'))

if __name__ == '__main__':
    unittest.main()