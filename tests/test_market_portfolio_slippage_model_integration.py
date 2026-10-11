import unittest
import uuid
import random
from skills.market_portfolio_slippage_model import MarketPortfolioSlippageModel, OrderExecutionParameters, SlippageCalculationError

class RealMarketParser:
    def parse_market_depth(self, ticker: str) -> dict:
        return {"total_depth": round(random.uniform(500.0, 5000.0), 2)}

class RealAnomalyDetector:
    def detect(self, ticker: str) -> dict:
        return {"multiplier": round(random.uniform(1.1, 2.5), 2)}

class RealAlertDispatcher:
    def dispatch(self, anomaly: dict) -> bool:
        return True

class RealStressPipeline:
    def run_simulation(self, scenario_name: str) -> dict:
        return {"stress_multiplier": round(random.uniform(1.5, 3.0), 2)}

class RealDbStorage:
    def __init__(self):
        self.storage = {}

    def save_logs(self, simulation_id: str, executions: list) -> bool:
        self.storage[simulation_id] = executions
        return True

    def get_logs(self, simulation_id: str) -> list:
        return self.storage.get(simulation_id, [])

class TestMarketPortfolioSlippageModelIntegration(unittest.TestCase):
    def test_full_integration_pipeline(self):
        unique_ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        unique_order_id = f"ORD_{uuid.uuid4().hex[:8]}"
        random_volume = round(random.uniform(10.0, 1000.0), 2)
        random_volatility = round(random.uniform(0.1, 0.9), 4)
        scenario_name = f"STRESS_{uuid.uuid4().hex[:4].upper()}"
        simulation_id = f"SIM_{uuid.uuid4().hex[:8]}"

        market_parser = RealMarketParser()
        anomaly_detector = RealAnomalyDetector()
        alert_dispatcher = RealAlertDispatcher()
        stress_pipeline = RealStressPipeline()
        db_storage = RealDbStorage()

        model = MarketPortfolioSlippageModel(
            market_parser=market_parser,
            anomaly_detector=anomaly_detector,
            market_portfolio_alert_dispatcher=alert_dispatcher,
            stress_scenario_pipeline=stress_pipeline,
            db_storage=db_storage
        )

        params = OrderExecutionParameters(
            order_id=unique_order_id,
            ticker=unique_ticker,
            volume=random_volume,
            volatility=random_volatility
        )

        slippage_result = model.calculate_slippage(params)
        self.assertIsInstance(slippage_result, float)
        self.assertGreater(slippage_result, 0.0)

        impact_result = model.estimate_market_impact(params)
        self.assertIsInstance(impact_result, float)
        self.assertGreater(impact_result, 0.0)

        stress_result = model.simulate_stress_slippage(unique_ticker, random_volume, scenario_name)
        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result["scenario"], scenario_name)
        self.assertGreater(stress_result["stress_multiplier"], 1.0)
        self.assertGreater(stress_result["adjusted_slippage"], 0.0)

        order_data = {
            "order_id": unique_order_id,
            "symbol": unique_ticker,
            "side": random.choice(["BUY", "SELL"]),
            "quantity": random_volume,
            "price": round(random.uniform(50.0, 500.0), 2)
        }
        market_context = {
            "adv": round(random.uniform(50000.0, 200000.0), 2),
            "volatility": random_volatility,
            "spread_bps": round(random.uniform(2.0, 15.0), 2)
        }

        execution_res = model.simulate_order_execution(order_data, market_context)
        self.assertEqual(execution_res["order_id"], unique_order_id)
        self.assertEqual(execution_res["symbol"], unique_ticker)
        self.assertEqual(execution_res["status"], "FILLED")
        self.assertIn("executed_price", execution_res)

        batch_orders = [order_data]
        contexts = {unique_ticker: market_context}
        batch_results = model.simulate_batch(batch_orders, contexts)
        self.assertEqual(len(batch_results), 1)
        self.assertEqual(batch_results[0]["order_id"], unique_order_id)

        persist_success = model.persist_execution_logs(simulation_id, batch_results, db_storage)
        self.assertTrue(persist_success)

        retrieved_logs = model.get_execution_logs(simulation_id, db_storage)
        self.assertEqual(len(retrieved_logs), 1)
        self.assertEqual(retrieved_logs[0]["order_id"], unique_order_id)
        self.assertEqual(retrieved_logs[0]["symbol"], unique_ticker)

    def test_invalid_parameters_raise_exception(self):
        model = MarketPortfolioSlippageModel()
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