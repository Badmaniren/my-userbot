import os
import random
import string
import unittest
import uuid

from skills.market_portfolio_tax_calculator import (
    MarketPortfolioTaxCalculator,
    calculate_portfolio_taxes,
)


class SimpleDbStorage:
    def __init__(self, data=None):
        self._data = data or {}

    def get_portfolio(self, portfolio_id):
        return self._data.get(portfolio_id)


class SimpleMarketParser:
    def parse_stream(self, stream):
        if isinstance(stream, dict) and "stream_id" in stream:
            return {"stream_id": stream["stream_id"]}
        return None


class DealObject:
    def __init__(self, deal_type, price, shares):
        self.type = deal_type
        self.price = price
        self.shares = shares


class TestMarketPortfolioTaxCalculatorIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())

    def test_calculate_tax_integration_with_db_storage(self):
        sell_price = round(random.uniform(150.0, 500.0), 2)
        purchase_price = round(random.uniform(50.0, 140.0), 2)
        shares = random.randint(1, 500)

        portfolio_record = {
            "sell_price": sell_price,
            "purchase_price": purchase_price,
            "shares": shares,
        }

        db_storage = SimpleDbStorage({self.portfolio_id: portfolio_record})
        calc = MarketPortfolioTaxCalculator(db_storage=db_storage)

        calculated_tax = calc.calculate_tax(self.portfolio_id)

        expected_profit = (sell_price - purchase_price) * shares
        expected_tax = round(expected_profit * 0.13, 2)

        self.assertEqual(calculated_tax, expected_tax)

    def test_calculate_tax_without_storage_or_missing_id(self):
        calc_no_db = MarketPortfolioTaxCalculator()
        self.assertEqual(calc_no_db.calculate_tax(self.portfolio_id), 0.0)

        empty_db = SimpleDbStorage()
        calc_empty_db = MarketPortfolioTaxCalculator(db_storage=empty_db)
        self.assertEqual(calc_empty_db.calculate_tax(self.portfolio_id), 0.0)

    def test_process_dividend_stream_integration(self):
        parser = SimpleMarketParser()
        calc = MarketPortfolioTaxCalculator(market_parser=parser)

        random_stream_id = "stream_" + "".join(random.choices(string.ascii_letters + string.digits, k=10))
        result = calc.process_dividend_stream({"stream_id": random_stream_id})
        self.assertEqual(result, random_stream_id)

        invalid_result = calc.process_dividend_stream("invalid_stream_data")
        self.assertIsNone(invalid_result)

    def test_calculate_portfolio_taxes_mixed_deals(self):
        holding_period = random.randint(30, 1095)
        dividends = round(random.uniform(100.0, 10000.0), 2)

        dict_sell_price = round(random.uniform(120.0, 300.0), 2)
        dict_sell_shares = random.randint(5, 50)

        obj_sell_price = round(random.uniform(130.0, 400.0), 2)
        obj_sell_shares = random.randint(10, 100)

        deals = [
            {"type": "SELL", "price": dict_sell_price, "shares": dict_sell_shares},
            {"type": "BUY", "price": 90.0, "shares": 100},
            DealObject("SELL", obj_sell_price, obj_sell_shares),
            DealObject("BUY", 85.0, 50),
        ]

        tax_report = calculate_portfolio_taxes(
            portfolio_id=self.portfolio_id,
            user_id=self.user_id,
            deals=deals,
            holding_period=holding_period,
            dividends=dividends,
        )

        dict_profit = (dict_sell_price - 100.0) * dict_sell_shares
        obj_profit = (obj_sell_price - 100.0) * obj_sell_shares
        expected_total_profit = dict_profit + obj_profit

        expected_tax = round(max(0.0, expected_total_profit * 0.13 + dividends * 0.13), 2)

        self.assertEqual(tax_report["portfolio_id"], self.portfolio_id)
        self.assertEqual(tax_report["user_id"], self.user_id)
        self.assertEqual(tax_report["total_tax_due"], expected_tax)


if __name__ == "__main__":
    unittest.main()