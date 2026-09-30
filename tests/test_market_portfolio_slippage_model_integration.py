import unittest
import uuid
import random
from skills.market_portfolio_slippage_model import MarketPortfolioSlippageModel, OrderExecutionParameters, SlippageCalculationError

class RealMarketParser:
    def parse_market_depth(self, ticker: str) -> dict:
        return {"total_depth": random.uniform(500.0, 5000.0)}

class RealAnomalyDetector:
    def detect(self, ticker: str) -> dict:
        return {"multiplier": random.uniform(1.0, 3.0), "ticker": ticker}

class RealAlertDispatcher:
    def dispatch(self, anomaly: dict) -> None:
        if not isinstance(anomaly, dict):
            raise ValueError("Invalid anomaly payload")

class RealStressScenarioPipeline:
    def run_simulation(self, scenario_name: str) -> dict:
        return {"stress_multiplier": random.uniform(1.5, 4.0), "scenario": scenario_name}

class RealDbStorage:
    def __init__(self):
        self.logs = {}

    def save_logs(self, simulation_id: str, executions: list) -> None:
        self.logs[simulation_id] = executions

    def get_logs(self, simulation_id: str) -> list:
        return self.logs.get(simulation_id, [])

class TestMarketPortfolioSlippageModelIntegration(unittest.TestCase):

    def setUp(self):
        self.market_parser = RealMarketParser()
        self.anomaly_detector = RealAnomalyDetector()
        self.alert_dispatcher = RealAlertDispatcher()
        self.stress_scenario_pipeline = RealStressScenarioPipeline()
        self.db_storage = RealDbStorage()

        self.model = MarketPortfolioSlippageModel(
            market_parser=self.market_parser,
            market_anomaly_detector=self.anomaly_detector,
            market_portfolio_alert_dispatcher=self.alert_dispatcher,
            market_portfolio_stress_scenario_pipeline=self.stress_scenario_pipeline,
            db_storage=self.db_storage
        )

    def test_end_to_end_slippage_and_simulation(self):
        random_ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        random_volume = round(random.uniform(100.0, 10000.0), 2)
        random_volatility = round(random.uniform(0.1, 0.9), 4)
        order_id = str(uuid.uuid4())

        params = OrderExecutionParameters(
            order_id=order_id,
            ticker=random_ticker,
            volume=random_volume,
            volatility=random_volatility
        )

        slippage = self.model.calculate_slippage(params)
        self.assertIsInstance(slippage, float)
        self.assertGreater(slippage, 0.0)

        impact = self.model.estimate_market_impact(params)
        self.assertIsInstance(impact, float)
        self.assertGreater(impact, 0.0)

        scenario_name = f"CRISIS_{uuid.uuid4().hex[:4].upper()}"
        stress_result = self.model.simulate_stress_slippage(random_ticker, random_volume, scenario_name)
        self.assertIsInstance(stress_result, dict)
        self.assertEqual(stress_result["scenario"], scenario_name)
        self.assertIn("adjusted_slippage", stress_result)

        order_data = {
            "order_id": order_id,
            "symbol": random_ticker,
            "side": random.choice(["BUY", "SELL"]),
            "quantity": random_volume,
            "price": round(random.uniform(50.0, 500.0), 2)
        }
        market_context = {
            "adv": random.randint(50000, 500000),
            "volatility": random_volatility,
            "spread_bps": round(random.uniform(1.0, 15.0), 2)
        }

        execution_res = self.model.simulate_order_execution(order_data, market_context)
        self.assertEqual(execution_res["order_id"], order_id)
        self.assertEqual(execution_res["symbol"], random_ticker)
        self.assertEqual(execution_res["status"], "FILLED")

        simulation_id = f"SIM_{uuid.uuid4().hex}"
        persisted = self.model.persist_execution_logs(simulation_id, [execution_res], self.db_storage)
        self.assertTrue(persisted)

        retrieved_logs = self.model.get_execution_logs(simulation_id, self.db_storage)
        self.assertEqual(len(retrieved_logs), 1)
        self.assertEqual(retrieved_logs[0]["order_id"], order_id)

    def test_strict_exception_handling(self):
        invalid_params = OrderExecutionParameters(
            order_id=str(uuid.uuid4()),
            ticker="",
            volume=-10.0,
            volatility=0.0
        )
        with self.assertRaises(SlippageCalculationError):
            self.model.calculate_slippage(invalid_params)

if __name__ == "__main__":
    unittest.main()