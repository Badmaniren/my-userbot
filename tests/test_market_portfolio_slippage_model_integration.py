import random
import unittest
import uuid
from skills.market_portfolio_slippage_model import MarketPortfolioSlippageModel
import skills.db_storage as db_storage


class TestMarketPortfolioSlippageModelIntegration(unittest.TestCase):

    def setUp(self):
        self.model = MarketPortfolioSlippageModel()
        self.test_run_id = str(uuid.uuid4())

    def test_buy_order_execution_slippage(self):
        order_id = f"ord-buy-{uuid.uuid4().hex[:8]}"
        symbol = f"ASSET_{uuid.uuid4().hex[:6].upper()}"
        base_price = round(random.uniform(50.0, 300.0), 2)
        quantity = random.randint(500, 2000)
        adv = random.randint(50000, 200000)
        volatility = round(random.uniform(0.15, 0.40), 4)
        spread_bps = round(random.uniform(2.0, 10.0), 2)

        order_data = {
            "order_id": order_id,
            "symbol": symbol,
            "side": "BUY",
            "quantity": quantity,
            "price": base_price,
        }
        market_context = {
            "adv": adv,
            "volatility": volatility,
            "spread_bps": spread_bps,
        }

        result = self.model.simulate_order_execution(order_data, market_context)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("order_id"), order_id)
        self.assertEqual(result.get("symbol"), symbol)
        self.assertEqual(result.get("side"), "BUY")
        self.assertEqual(result.get("quantity"), quantity)
        self.assertEqual(result.get("status"), "FILLED")

        executed_price = result.get("executed_price")
        self.assertIsNotNone(executed_price)
        self.assertGreater(
            executed_price,
            base_price,
            f"Buy order execution price ({executed_price}) should exceed base price ({base_price}) due to slippage and spread",
        )

        slippage_bps = result.get("slippage_bps")
        self.assertIsNotNone(slippage_bps)
        self.assertGreater(slippage_bps, 0.0)

        market_impact = result.get("market_impact")
        self.assertIsNotNone(market_impact)
        self.assertGreater(market_impact, 0.0)

    def test_sell_order_execution_slippage(self):
        order_id = f"ord-sell-{uuid.uuid4().hex[:8]}"
        symbol = f"ASSET_{uuid.uuid4().hex[:6].upper()}"
        base_price = round(random.uniform(80.0, 450.0), 2)
        quantity = random.randint(300, 1500)
        adv = random.randint(40000, 150000)
        volatility = round(random.uniform(0.20, 0.50), 4)
        spread_bps = round(random.uniform(3.0, 8.0), 2)

        order_data = {
            "order_id": order_id,
            "symbol": symbol,
            "side": "SELL",
            "quantity": quantity,
            "price": base_price,
        }
        market_context = {
            "adv": adv,
            "volatility": volatility,
            "spread_bps": spread_bps,
        }

        result = self.model.simulate_order_execution(order_data, market_context)

        self.assertEqual(result.get("order_id"), order_id)
        self.assertEqual(result.get("symbol"), symbol)
        self.assertEqual(result.get("side"), "SELL")

        executed_price = result.get("executed_price")
        self.assertIsNotNone(executed_price)
        self.assertLess(
            executed_price,
            base_price,
            f"Sell order execution price ({executed_price}) should be less than base price ({base_price})",
        )
        self.assertGreater(result.get("slippage_bps"), 0.0)

    def test_market_impact_scales_with_order_size(self):
        symbol = f"SCALE_{uuid.uuid4().hex[:6].upper()}"
        base_price = round(random.uniform(100.0, 200.0), 2)
        adv = 100000
        volatility = 0.25
        spread_bps = 5.0

        small_qty = 200
        large_qty = 15000

        market_context = {
            "adv": adv,
            "volatility": volatility,
            "spread_bps": spread_bps,
        }

        small_order = {
            "order_id": f"ord-sm-{uuid.uuid4().hex[:6]}",
            "symbol": symbol,
            "side": "BUY",
            "quantity": small_qty,
            "price": base_price,
        }
        large_order = {
            "order_id": f"ord-lg-{uuid.uuid4().hex[:6]}",
            "symbol": symbol,
            "side": "BUY",
            "quantity": large_qty,
            "price": base_price,
        }

        small_res = self.model.simulate_order_execution(small_order, market_context)
        large_res = self.model.simulate_order_execution(large_order, market_context)

        self.assertGreater(
            large_res["market_impact"],
            small_res["market_impact"],
            "Market impact of 15% ADV order must be strictly greater than 0.2% ADV order",
        )
        self.assertGreater(
            large_res["slippage_bps"],
            small_res["slippage_bps"],
            "Slippage bps for larger participation must exceed smaller participation",
        )
        self.assertGreater(
            large_res["executed_price"],
            small_res["executed_price"],
            "Executed buy price for large order must be higher than for small order",
        )

    def test_volatility_sensitivity(self):
        symbol = f"VOL_{uuid.uuid4().hex[:6].upper()}"
        base_price = 150.0
        quantity = 2500
        adv = 80000
        spread_bps = 4.0

        low_vol_context = {"adv": adv, "volatility": 0.10, "spread_bps": spread_bps}
        high_vol_context = {"adv": adv, "volatility": 0.60, "spread_bps": spread_bps}

        order = {
            "order_id": f"ord-vol-{uuid.uuid4().hex[:6]}",
            "symbol": symbol,
            "side": "BUY",
            "quantity": quantity,
            "price": base_price,
        }

        low_vol_res = self.model.simulate_order_execution(order, low_vol_context)
        high_vol_res = self.model.simulate_order_execution(order, high_vol_context)

        self.assertGreater(
            high_vol_res["market_impact"],
            low_vol_res["market_impact"],
            "Higher volatility environment must generate higher market impact",
        )

    def test_batch_simulation_and_db_integration(self):
        orders_batch = []
        contexts = {}
        unique_order_ids = set()

        for _ in range(5):
            oid = f"batch-{uuid.uuid4().hex}"
            sym = f"SYM_{uuid.uuid4().hex[:4].upper()}"
            side = random.choice(["BUY", "SELL"])
            qty = random.randint(100, 3000)
            px = round(random.uniform(30.0, 500.0), 2)
            unique_order_ids.add(oid)

            orders_batch.append({
                "order_id": oid,
                "symbol": sym,
                "side": side,
                "quantity": qty,
                "price": px,
            })
            contexts[sym] = {
                "adv": random.randint(50000, 250000),
                "volatility": round(random.uniform(0.18, 0.35), 4),
                "spread_bps": round(random.uniform(1.5, 6.0), 2),
            }

        execution_results = self.model.simulate_batch(orders_batch, contexts)

        self.assertEqual(len(execution_results), len(orders_batch))

        executed_ids = {res["order_id"] for res in execution_results}
        self.assertEqual(executed_ids, unique_order_ids)

        for res in execution_results:
            self.assertIn("realized_cost", res)
            self.assertIn("effective_slippage", res)
            self.assertGreater(res["realized_cost"], 0.0)

        logged = self.model.persist_execution_logs(
            simulation_id=self.test_run_id,
            executions=execution_results,
            storage=db_storage,
        )
        self.assertTrue(logged)

        retrieved_logs = self.model.get_execution_logs(
            simulation_id=self.test_run_id,
            storage=db_storage,
        )
        self.assertIsInstance(retrieved_logs, list)
        self.assertEqual(len(retrieved_logs), len(orders_batch))
        retrieved_ids = {r["order_id"] for r in retrieved_logs}
        self.assertEqual(retrieved_ids, unique_order_ids)


if __name__ == "__main__":
    unittest.main()