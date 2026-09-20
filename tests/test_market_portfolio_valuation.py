import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import os

from skills.market_portfolio_valuation import PortfolioValuation

class TestMarketPortfolioValuation(unittest.TestCase):

    def setUp(self):
        self.random_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_url = f"https://{uuid.uuid4().hex}.com/{random.randint(1000, 9999)}"
        self.random_storage = f"{uuid.uuid4().hex}.json"
        self.random_price = round(random.uniform(10.0, 1000.0), 2)
        self.random_quantity = round(random.uniform(1.0, 100.0), 4)
        self.random_buy_price = round(random.uniform(5.0, 900.0), 2)

    @patch('skills.market_portfolio_valuation.MarketParser')
    @patch('skills.market_portfolio_valuation.db_storage')
    def test_calculate_portfolio_value_and_pnl(self, mock_db, mock_parser_class):
        mock_parser_instance = mock_parser_class.return_value
        mock_parser_instance.fetch_price.return_value = self.random_price

        mock_db.load_portfolio.return_value = {
            self.random_symbol: {
                "quantity": self.random_quantity,
                "buy_price": self.random_buy_price
            }
        }

        valuator = PortfolioValuation(storage_file=self.random_storage)
        result = valuator.evaluate_portfolio(self.random_url)

        self.assertIn(self.random_symbol, result)
        symbol_data = result[self.random_symbol]
        
        expected_current_value = round(self.random_quantity * self.random_price, 2)
        expected_invested = round(self.random_quantity * self.random_buy_price, 2)
        expected_pnl = round(expected_current_value - expected_invested, 2)
        expected_pnl_percent = round((expected_pnl / expected_invested) * 100, 2) if expected_invested > 0 else 0.0

        self.assertEqual(symbol_data["current_price"], self.random_price)
        self.assertEqual(symbol_data["current_value"], expected_current_value)
        self.assertEqual(symbol_data["invested"], expected_invested)
        self.assertEqual(symbol_data["pnl"], expected_pnl)
        self.assertEqual(symbol_data["pnl_percent"], expected_pnl_percent)

    @patch('skills.market_portfolio_valuation.MarketParser')
    @patch('skills.market_portfolio_valuation.db_storage')
    def test_evaluate_portfolio_empty_storage(self, mock_db, mock_parser_class):
        mock_db.load_portfolio.return_value = {}

        valuator = PortfolioValuation(storage_file=self.random_storage)
        result = valuator.evaluate_portfolio(self.random_url)

        self.assertEqual(result, {})
        mock_parser_class.return_value.fetch_price.assert_not_called()

    @patch('skills.market_portfolio_valuation.MarketParser')
    @patch('skills.market_portfolio_valuation.db_storage')
    def test_evaluate_portfolio_parser_failure(self, mock_db, mock_parser_class):
        mock_parser_instance = mock_parser_class.return_value
        mock_parser_instance.fetch_price.side_effect = Exception(uuid.uuid4().hex)

        mock_db.load_portfolio.return_value = {
            self.random_symbol: {
                "quantity": self.random_quantity,
                "buy_price": self.random_buy_price
            }
        }

        valuator = PortfolioValuation(storage_file=self.random_storage)
        result = valuator.evaluate_portfolio(self.random_url)

        self.assertIn(self.random_symbol, result)
        self.assertIn("error", result[self.random_symbol])

    @patch('skills.market_portfolio_valuation.MarketParser')
    @patch('skills.market_portfolio_valuation.db_storage')
    def test_total_portfolio_summary(self, mock_db, mock_parser_class):
        symbol_one = ''.join(random.choices(string.ascii_uppercase, k=4))
        symbol_two = ''.join(random.choices(string.ascii_uppercase, k=4))
        
        price_one = 100.0
        price_two = 200.0
        
        qty_one = 2.0
        qty_two = 3.0
        
        buy_one = 80.0
        buy_two = 150.0

        mock_parser_instance = mock_parser_class.return_value
        mock_parser_instance.fetch_price.side_effect = [price_one, price_two]

        mock_db.load_portfolio.return_value = {
            symbol_one: {"quantity": qty_one, "buy_price": buy_one},
            symbol_two: {"quantity": qty_two, "buy_price": buy_two}
        }

        valuator = PortfolioValuation(storage_file=self.random_storage)
        summary = valuator.get_total_summary(self.random_url)

        expected_total_value = (qty_one * price_one) + (qty_two * price_two)
        expected_total_invested = (qty_one * buy_one) + (qty_two * buy_two)
        expected_total_pnl = expected_total_value - expected_total_invested

        self.assertEqual(summary["total_value"], expected_total_value)
        self.assertEqual(summary["total_invested"], expected_total_invested)
        self.assertEqual(summary["total_pnl"], expected_total_pnl)

if __name__ == '__main__':
    unittest.main()