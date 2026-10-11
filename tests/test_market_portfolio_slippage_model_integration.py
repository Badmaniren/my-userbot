import unittest
import uuid
import random
from skills.market_portfolio_slippage_model import MarketPortfolioSlippageModel, OrderExecutionParameters, SlippageCalculationError

class RealMarketPortfolioSlippageModelIntegrationTest(unittest.TestCase):
    def test_full_integration_pipeline_and_square_root_law(self):
        rand_suffix = uuid.uuid4().hex[:8]
        test_ticker = f"TEST_{rand_suffix}"
        test_order_id = f"ORD_{rand_suffix}"
        test_volume = float(random.randint(1000, 50000))
        test_volatility = round(random.uniform(0.1, 0.5), 4)
        test_base_price = round(random.uniform(50.0, 500.0), 2)
        test_adv = float(random.randint(200000, 1000000))
        test_spread = float(random.randint(2, 15))
        
        class RealDummyStorage:
            def __init__(self):
                self.storage_dict = {}
                self.saved_logs_called = False

            def save_logs(self, simulation_id, executions):
                self.storage_dict[simulation_id] = executions
                self.saved_logs_called = True

            def get_logs(self, simulation_id):
                return self.storage_dict.get(simulation_id, [])

        class RealDummyMarketParser:
            def parse_market_depth(self, ticker):
                return {"total_depth": test_volume * 0.5}

        class RealDummyAnomalyDetector:
            def detect(self, ticker):
                return {"multiplier": 1.5}

        class RealDummyAlertDispatcher:
            def __init__(self):
                self.dispatched = False
            def dispatch(self, anomaly):
                self.dispatched = True

        class RealDummyStressPipeline:
            def run_simulation(self, scenario_name):
                return {"stress_multiplier": 1.8}

        storage = RealDummyStorage()
        market_parser = RealDummyMarketParser()
        anomaly_detector = RealDummyAnomalyDetector()
        alert_dispatcher = RealDummyAlertDispatcher()
        stress_pipeline = RealDummyStressPipeline()

        model = MarketPortfolioSlippageModel(
            db_storage=storage,
            market_parser=market_parser,
            anomaly_detector=anomaly_detector,
            alert_dispatcher=alert_dispatcher,
            stress_scenario_pipeline=stress_pipeline
        )

        order_params = OrderExecutionParameters(
            order_id=test_order_id,
            ticker=test_ticker,
            volume=test_volume,
            volatility=test_volatility
        )

        slippage = model.calculate_slippage(order_params)
        self.assertIsInstance(slippage, float)
        self.assertGreater(slippage, 0.0)

        impact = model.estimate_market_impact(order_params)
        self.assertIsInstance(impact, float)
        self.assertGreater(impact, 0.0)
        self.assertTrue(alert_dispatcher.dispatched)

        stress_result = model.simulate_stress_slippage(test_ticker, test_volume, f"crisis_{rand_suffix}")
        self.assertIn("scenario", stress_result)
        self.assertEqual(stress_result["stress_multiplier"], 1.8)
        self.assertGreater(stress_result["adjusted_slippage"], 0.0)

        order_data = {
            "order_id": test_order_id,
            "symbol": test_ticker,
            "side": "BUY",
            "quantity": test_volume,
            "price": test_base_price
        }
        market_context = {
            "adv": test_adv,
            "volatility": test_volatility,
            "spread_bps": test_spread
        }

        execution_res = model.simulate_order_execution(order_data, market_context)
        self.assertEqual(execution_res["order_id"], test_order_id)
        self.assertEqual(execution_res["symbol"], test_ticker)
        self.assertEqual(execution_res["status"], "FILLED")
        self.assertGreater(execution_res["market_impact"], 0.0)
        self.assertGreater(execution_res["executed_price"], test_base_price)

        batch_orders = [
            {
                "order_id": f"BATCH_{uuid.uuid4().hex[:6]}",
                "symbol": test_ticker,
                "side": "SELL",
                "quantity": float(random.randint(500, 10000)),
                "price": test_base_price
            }
        ]
        contexts = {test_ticker: market_context}
        batch_results = model.simulate_batch(batch_orders, contexts)
        self.assertEqual(len(batch_results), 1)
        self.assertEqual(batch_results[0]["status"], "FILLED")

        sim_id = f"SIM_{rand_suffix}"
        persist_success = model.persist_execution_logs(sim_id, batch_results, storage)
        self.assertTrue(persist_success)
        self.assertTrue(storage.saved_logs_called)

        fetched_logs = model.get_execution_logs(sim_id, storage)
        self.assertEqual(len(fetched_logs), 1)
        self.assertEqual(fetched_logs[0]["order_id"], batch_orders[0]["order_id"])

        invalid_params = OrderExecutionParameters(
            order_id="",
            ticker="",
            volume=-10.0,
            volatility=0.0
        )
        with self.assertRaises(SlippageCalculationError):
            model.calculate_slippage(invalid_params)

if __name__ == "__main__":
    unittest.main()