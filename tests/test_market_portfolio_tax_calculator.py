import unittest
from unittest.mock import patch
import random
import uuid
import io

from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator, calculate_portfolio_taxes


class TestMarketPortfolioTaxCalculator(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        self.calc = MarketPortfolioTaxCalculator()

    def test_calculate_tax_no_storage(self):
        calc_empty = MarketPortfolioTaxCalculator()
        res = calc_empty.calculate_tax(self.portfolio_id)
        self.assertEqual(res, 0.0)

    def test_calculate_tax_with_storage(self):
        buy_price = round(random.uniform(10.0, 100.0), 2)
        sell_price = round(buy_price + random.uniform(5.0, 50.0), 2)
        shares = random.randint(1, 100)

        mock_storage = type('MockStorage', (), {
            'get_portfolio': lambda self, pid: {
                "purchase_price": buy_price,
                "sell_price": sell_price,
                "shares": shares
            }
        })()

        self.calc.db_storage = mock_storage
        expected_profit = (sell_price - buy_price) * shares
        expected_tax = round(expected_profit * 0.13, 2)

        res = self.calc.calculate_tax(self.portfolio_id)
        self.assertEqual(res, expected_tax)

    def test_process_dividend_stream(self):
        stream_id = str(uuid.uuid4())
        stream = io.BytesIO(uuid.uuid4().bytes)

        mock_parser = type('MockParser', (), {
            'parse_stream': lambda self, s: {"stream_id": stream_id}
        })()

        self.calc.market_parser = mock_parser
        res = self.calc.process_dividend_stream(stream)
        self.assertEqual(res, stream_id)

    def test_process_dividend_stream_no_parser(self):
        stream = io.BytesIO(uuid.uuid4().bytes)
        res = self.calc.process_dividend_stream(stream)
        self.assertIsNone(res)

    def test_calculate_portfolio_taxes_fifo(self):
        price1 = round(random.uniform(50.0, 100.0), 2)
        price2 = round(price1 + 10.0, 2)
        sell_price = round(price2 + 20.0, 2)
        shares_cnt = random.randint(5, 20)

        deals = [
            {"type": "BUY", "price": price1, "shares": shares_cnt},
            {"type": "BUY", "price": price2, "shares": shares_cnt},
            {"type": "SELL", "price": sell_price, "shares": shares_cnt * 2}
        ]

        dividends = round(random.uniform(10.0, 100.0), 2)
        holding_period = random.randint(30, 400)

        result = calculate_portfolio_taxes(self.portfolio_id, self.user_id, deals, holding_period, dividends)

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["user_id"], self.user_id)
        self.assertGreater(result["total_tax_due"], 0.0)

    def test_calculate_portfolio_taxes_lifo(self):
        deals = [
            {"type": "BUY", "price": 100.0, "shares": 10},
            {"type": "BUY", "price": 200.0, "shares": 10},
            {"type": "SELL", "price": 250.0, "shares": 10}
        ]
        result = calculate_portfolio_taxes(self.portfolio_id, self.user_id, deals, 100, 0.0, method="LIFO")
        self.assertEqual(result["total_profit"], 500.0)
        self.assertEqual(result["total_tax_due"], round(500.0 * 0.13, 2))

    def test_calculate_portfolio_taxes_with_commissions(self):
        deals = [
            {"type": "BUY", "price": 100.0, "shares": 10, "commission": 10.0},
            {"type": "SELL", "price": 200.0, "shares": 10, "commission": 15.0}
        ]
        result = calculate_portfolio_taxes(self.portfolio_id, self.user_id, deals, 100, 0.0, commissions=5.0)
        self.assertEqual(result["total_profit"], 1000.0)
        self.assertEqual(result["total_commissions"], 30.0)
        self.assertEqual(result["net_profit"], 970.0)
        self.assertEqual(result["total_tax_due"], round(970.0 * 0.13, 2))

    def test_calculate_tax_gross_dividend(self):
        gross = 1000.0
        tax_rate = 0.15
        tax = self.calc.calculate_tax(gross, tax_rate)
        self.assertEqual(tax, 150.0)

    def test_calculate_portfolio_taxes_empty_deals(self):
        dividends = round(random.uniform(1.0, 50.0), 2)
        result = calculate_portfolio_taxes(self.portfolio_id, self.user_id, [], 100, dividends)
        expected_tax = round(dividends * 0.13, 2)
        self.assertEqual(result["total_tax_due"], expected_tax)

    def test_calculate_portfolio_taxes_object_deals(self):
        class DealObj:
            def __init__(self, dtype, price, shares):
                self.type = dtype
                self.price = price
                self.shares = shares

        p_buy = round(random.uniform(10.0, 50.0), 2)
        p_sell = round(p_buy + 30.0, 2)
        sh = random.randint(1, 10)

        deals = [
            DealObj("BUY", p_buy, sh),
            DealObj("SELL", p_sell, sh)
        ]

        result = calculate_portfolio_taxes(self.portfolio_id, self.user_id, deals, 180, 0.0)
        expected_profit = (p_sell - p_buy) * sh
        expected_tax = round(expected_profit * 0.13, 2)
        self.assertEqual(result["total_tax_due"], expected_tax)


if __name__ == '__main__':
    unittest.main()