import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
from skills.market_portfolio_allocation_balancer import MarketPortfolioAllocationBalancer


class TestMarketPortfolioAllocationBalancer(unittest.TestCase):

    def setUp(self):
        self.db_storage_mock = MagicMock()
        self.balancer = MarketPortfolioAllocationBalancer(db_storage=self.db_storage_mock)

    def test_balance_invalid_portfolio_data_type(self):
        rand_invalid_data = [random.randint(1, 100), str(uuid.uuid4())]
        for invalid_input in rand_invalid_data:
            with self.subTest(invalid_input=invalid_input):
                with self.assertRaises(ValueError):
                    self.balancer.balance(invalid_input)

    def test_balance_empty_portfolio_data(self):
        empty_data = {}
        res = self.balancer.balance(empty_data)
        self.assertEqual(res, {})

    def test_balance_single_asset_success(self):
        asset_id = uuid.uuid4().hex
        target_weight = round(random.uniform(0.1, 1.0), 2)
        current_price = round(random.uniform(10.0, 500.0), 2)
        liquidity = random.randint(5000, 50000)

        portfolio_data = {
            asset_id: {
                "target_weight": target_weight,
                "current_price": current_price,
                "liquidity": liquidity
            }
        }

        expected_shares = int((liquidity * target_weight) / current_price)
        if expected_shares < 1:
            expected_shares = 1

        result = self.balancer.balance(portfolio_data)

        self.assertIn(asset_id, result)
        self.assertEqual(result[asset_id]["allocated_shares"], expected_shares)
        self.assertEqual(result[asset_id]["status"], "success")

    def test_balance_multiple_assets_with_edge_cases(self):
        asset_id_1 = uuid.uuid4().hex
        asset_id_2 = uuid.uuid4().hex

        portfolio_data = {
            asset_id_1: {
                "weight": 0.5,
                "current_price": 0.0,
                "liquidity": 1000
            },
            asset_id_2: {
                "target_weight": 0.0,
                "current_price": 50.0,
                "liquidity": 100
            },
            uuid.uuid4().hex: "not_a_dict"
        }

        result = self.balancer.balance(portfolio_data)

        self.assertIn(asset_id_1, result)
        self.assertEqual(result[asset_id_1]["allocated_shares"], 500)

        self.assertIn(asset_id_2, result)
        self.assertEqual(result[asset_id_2]["allocated_shares"], 1)

    def test_balance_empty_result_fallback(self):
        asset_id = uuid.uuid4().hex
        portfolio_data = {
            asset_id: "invalid_inner_data"
        }

        result = self.balancer.balance(portfolio_data)
        self.assertEqual(result, {"status": "success"})


if __name__ == "__main__":
    unittest.main()