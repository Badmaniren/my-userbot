import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_valuation import PortfolioValuation

class TestPortfolioValuation(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.json"
        self.url = f"http://{uuid.uuid4().hex}.com/api"
        self.symbol_1 = uuid.uuid4().hex[:6].upper()
        self.symbol_2 = uuid.uuid4().hex[:6].upper()
        self.evaluator = PortfolioValuation(storage_file=self.storage_file)

    def test_load_data_with_load_portfolio(self):
        expected_data = {self.symbol_1: {"quantity": round(random.uniform(1.0, 100.0), 2)}}
        with patch('skills.market_portfolio_valuation.db_storage') as mock_db:
            if hasattr(mock_db, 'load_portfolio'):
                delattr(mock_db, 'load_portfolio')
            if not hasattr(mock_db, 'load_portfolio'):
                mock_db.load_portfolio = MagicMock(return_value=expected_data)

            result = self.evaluator.load_data(self.storage_file)
            self.assertEqual(result, expected_data)

    def test_load_data_with_load_data(self):
        expected_data = {self.symbol_2: {"quantity": round(random.uniform(1.0, 100.0), 2)}}
        with patch('skills.market_portfolio_valuation.db_storage') as mock_db:
            if hasattr(mock_db, 'load_portfolio'):
                delattr(mock_db, 'load_portfolio')
            if hasattr(mock_db, 'load_data'):
                delattr(mock_db, 'load_data')
            mock_db.load_data = MagicMock(return_value=expected_data)

            result = self.evaluator.load_data(self.storage_file)
            self.assertEqual(result, expected_data)

    def test_load_data_empty(self):
        with patch('skills.market_portfolio_valuation.db_storage') as mock_db:
            if hasattr(mock_db, 'load_portfolio'):
                delattr(mock_db, 'load_portfolio')
            if hasattr(mock_db, 'load_data'):
                delattr(mock_db, 'load_data')

            result = self.evaluator.load_data(self.storage_file)
            self.assertEqual(result, {})

    def test_evaluate_portfolio_empty(self):
        with patch.object(self.evaluator, 'load_data', return_value={}):
            result = self.evaluator.evaluate_portfolio(self.url)
            self.assertEqual(result, {})

    def test_evaluate_portfolio_success(self):
        quantity = round(random.uniform(10.0, 50.0), 2)
        buy_price = round(random.uniform(100.0, 200.0), 2)
        current_price = round(buy_price * random.uniform(1.1, 1.5), 2)

        portfolio_data = {
            self.symbol_1: {
                "quantity": quantity,
                "buy_price": buy_price
            }
        }

        with patch.object(self.evaluator, 'load_data', return_value=portfolio_data):
            with patch('skills.market_portfolio_valuation.MarketParser') as MockParser:
                instance = MockParser.return_value
                instance.fetch_price.return_value = current_price

                result = self.evaluator.evaluate_portfolio(self.url)

                self.assertIn(self.symbol_1, result)
                self.assertEqual(result[self.symbol_1]["current_price"], current_price)
                expected_current_value = round(quantity * current_price, 2)
                expected_invested = round(quantity * buy_price, 2)
                expected_pnl = round(expected_current_value - expected_invested, 2)

                self.assertEqual(result[self.symbol_1]["current_value"], expected_current_value)
                self.assertEqual(result[self.symbol_1]["invested"], expected_invested)
                self.assertEqual(result[self.symbol_1]["pnl"], expected_pnl)

    def test_evaluate_portfolio_fetch_error(self):
        error_msg = uuid.uuid4().hex
        portfolio_data = {
            self.symbol_1: {
                "quantity": 10.0,
                "buy_price": 100.0
            }
        }

        with patch.object(self.evaluator, 'load_data', return_value=portfolio_data):
            with patch('skills.market_portfolio_valuation.MarketParser') as MockParser:
                instance = MockParser.return_value
                instance.fetch_price.side_effect = Exception(error_msg)

                result = self.evaluator.evaluate_portfolio(self.url)

                self.assertIn(self.symbol_1, result)
                self.assertIn("error", result[self.symbol_1])
                self.assertEqual(result[self.symbol_1]["error"], error_msg)

    def test_get_total_summary(self):
        evaluated_data = {
            self.symbol_1: {
                "current_value": 1500.0,
                "invested": 1000.0,
                "pnl": 500.0
            },
            self.symbol_2: {
                "error": "some error"
            }
        }

        with patch.object(self.evaluator, 'evaluate_portfolio', return_value=evaluated_data):
            summary = self.evaluator.get_total_summary(self.url)

            self.assertEqual(summary["total_value"], 1500.0)
            self.assertEqual(summary["total_invested"], 1000.0)
            self.assertEqual(summary["total_pnl"], 500.0)

    def test_calculate_portfolio_pnl(self):
        expected_summary = {
            "total_value": round(random.uniform(1000.0, 5000.0), 2),
            "total_invested": round(random.uniform(500.0, 1000.0), 2),
            "total_pnl": round(random.uniform(100.0, 4000.0), 2)
        }

        with patch.object(self.evaluator, 'get_total_summary', return_value=expected_summary):
            result = self.evaluator.calculate_portfolio_pnl(self.url)
            self.assertEqual(result, expected_summary)

if __name__ == '__main__':
    unittest.main()