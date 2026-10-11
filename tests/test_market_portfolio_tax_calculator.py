import unittest
from unittest.mock import patch
import random
import uuid
import io

from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator, calculate_portfolio_taxes


class TestMarketPortfolioTaxCalculator(unittest.TestCase):

    def setUp(self):
        self.portfolio_id_val = str(uuid.uuid4())
        self.user_id_val = str(uuid.uuid4())
        self.sell_price = round(random.uniform(150.0, 500.0), 2)
        self.purchase_price = round(random.uniform(50.0, 149.0), 2)
        self.shares_count = random.randint(1, 50)
        self.dividends_val = round(random.uniform(10.0, 1000.0), 2)

    def test_init_and_calculate_tax_no_storage(self):
        calc = MarketPortfolioTaxCalculator()
        res = calc.calculate_tax(self.portfolio_id_val)
        self.assertEqual(res, 0.0)

    def test_calculate_tax_with_mock_storage(self):
        mock_storage = unittest.mock.MagicMock()
        mock_storage.get_portfolio.return_value = {
            "sell_price": self.sell_price,
            "purchase_price": self.purchase_price,
            "shares": self.shares_count
        }
        calc = MarketPortfolioTaxCalculator(db_storage=mock_storage)
        expected_profit = (self.sell_price - self.purchase_price) * self.shares_count
        expected_tax = round(expected_profit * 0.13, 2)

        res = calc.calculate_tax(self.portfolio_id_val)
        self.assertEqual(res, expected_tax)
        mock_storage.get_portfolio.assert_called_once_with(self.portfolio_id_val)

    def test_calculate_tax_empty_portfolio(self):
        mock_storage = unittest.mock.MagicMock()
        mock_storage.get_portfolio.return_value = None
        calc = MarketPortfolioTaxCalculator(db_storage=mock_storage)
        res = calc.calculate_tax(self.portfolio_id_val)
        self.assertEqual(res, 0.0)

    def test_process_dividend_stream(self):
        stream_id_val = str(uuid.uuid4())
        mock_parser = unittest.mock.MagicMock()
        mock_parser.parse_stream.return_value = {"stream_id": stream_id_val}
        calc = MarketPortfolioTaxCalculator(market_parser=mock_parser)

        stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        res = calc.process_dividend_stream(stream_data)
        self.assertEqual(res, stream_id_val)
        mock_parser.parse_stream.assert_called_once_with(stream_data)

    def test_process_dividend_stream_invalid_parser(self):
        calc = MarketPortfolioTaxCalculator()
        stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        res = calc.process_dividend_stream(stream_data)
        self.assertIsNone(res)

    def test_calculate_portfolio_taxes_dict_deals(self):
        deal_price = 200.0
        deal_shares = 10
        deals = [
            {"type": "SELL", "price": deal_price, "shares": deal_shares},
            {"type": "BUY", "price": 50.0, "shares": 10}
        ]
        res = calculate_portfolio_taxes(self.portfolio_id_val, self.user_id_val, deals, 365, self.dividends_val)

        profit = (deal_price - 100.0) * deal_shares
        expected_tax = round(max(0.0, profit * 0.13 + self.dividends_val * 0.13), 2)

        self.assertEqual(res["portfolio_id"], self.portfolio_id_val)
        self.assertEqual(res["user_id"], self.user_id_val)
        self.assertEqual(res["total_tax_due"], expected_tax)

    def test_calculate_portfolio_taxes_object_deals(self):
        class DealObj:
            def __init__(self, t, p, s):
                self.type = t
                self.price = p
                self.shares = s

        deal_price = 250.0
        deal_shares = 5
        deals = [DealObj("SELL", deal_price, deal_shares)]

        res = calculate_portfolio_taxes(self.portfolio_id_val, self.user_id_val, deals, 100, 0.0)
        profit = (deal_price - 100.0) * deal_shares
        expected_tax = round(max(0.0, profit * 0.13), 2)

        self.assertEqual(res["total_tax_due"], expected_tax)

    def test_calculate_portfolio_taxes_none_values(self):
        deals = [
            {"type": "SELL", "price": None, "shares": None}
        ]
        res = calculate_portfolio_taxes(self.portfolio_id_val, self.user_id_val, deals, 10, 0.0)
        self.assertEqual(res["total_tax_due"], 0.0)


class TestMarketPortfolioTaxCalculatorIntegration(unittest.TestCase):

    def test_integration_flow(self):
        portfolio_id = uuid.uuid4().hex
        user_id = uuid.uuid4().hex
        stream_id = uuid.uuid4().hex

        mock_storage = unittest.mock.MagicMock()
        mock_storage.get_portfolio.return_value = {
            "sell_price": 300.0,
            "purchase_price": 100.0,
            "shares": 10
        }

        mock_parser = unittest.mock.MagicMock()
        mock_parser.parse_stream.return_value = {"stream_id": stream_id}

        calc = MarketPortfolioTaxCalculator(
            db_storage=mock_storage,
            market_parser=mock_parser
        )

        tax_res = calc.calculate_tax(portfolio_id)
        self.assertEqual(tax_res, 260.0)

        stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        stream_res = calc.process_dividend_stream(stream_data)
        self.assertEqual(stream_res, stream_id)

        deals = [{"type": "SELL", "price": 300.0, "shares": 10}]
        portfolio_tax = calculate_portfolio_taxes(portfolio_id, user_id, deals, 400, 50.0)
        self.assertEqual(portfolio_tax["portfolio_id"], portfolio_id)
        self.assertEqual(portfolio_tax["user_id"], user_id)
        self.assertEqual(portfolio_tax["total_tax_due"], round((200.0 * 10 * 0.13) + (50.0 * 0.13), 2))


if __name__ == '__main__':
    unittest.main()