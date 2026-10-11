import unittest
import uuid
import random
from skills.market_portfolio_slippage_model import (
    MarketPortfolioSlippageModel,
    OrderExecutionParameters,
    SlippageCalculationError
)


class RealMarketParser:
    def parse_market_depth(self, ticker: str) -> dict:
        return {"total_depth": 500.0}


class RealAnomalyDetector:
    def detect(self, ticker: str) -> dict:
        return {"multiplier": 1.5}


class RealAlertDispatcher:
    def __init__(self):
        self.dispatched = []

    def dispatch(self, anomaly: dict):
        self.dispatched.append(anomaly)


class RealStressPipeline:
    def run_simulation(self, scenario_name: str) -> dict:
        return {"stress_multiplier": 2.2}


class RealDbStorage:
    def __init__(self):
        self.storage = {}

    def save_logs(self, simulation_id: str, executions: list):
        self.storage[simulation_id] = executions

    def get_log(self, simulation_id: str):
        return self.storage.get(simulation_id, [])


class IntegrationTestMarketPortfolioSlippageModel(unittest.TestCase):

    def setUp(self):
        self.market_parser = RealMarketParser()
        self.anomaly_detector = RealAnomalyDetector()
        self.alert_dispatcher = RealAlertDispatcher()
        self.stress_scenario_pipeline = RealStressPipeline()
        self.db_storage = RealDbStorage()

        self.model = MarketPortfolioSlippageModel(
            market_parser=self.market_parser,
            anomaly_detector=self.anomaly_detector,
            alert_dispatcher=self.alert_dispatcher,
            stress_scenario_pipeline=self.stress_scenario_pipeline,
            db_storage=self.db_storage
        )

    def test_calculate_slippage_integration(self):
        rand_order_id = str(uuid.uuid4())
        rand_ticker = f"TICKER_{random.randint(1000, 9999)}"
        rand_volume = round(random.uniform(10.0, 1000.0), 2)
        rand_volatility = round(random.uniform(0.1, 0.9), 4)

        params = OrderExecutionParameters(
            order_id=rand_order_id,
            ticker=rand_ticker,
            volume=rand_volume,
            volatility=rand_volatility
        )

        result_slippage = self.model.calculate_slippage(params)
        self.assertIsInstance(result_slippage, float)
        self.assertGreater(result_slippage, 0.0)

    def test_estimate_market_impact_integration(self):
        rand_order_id = str(uuid.uuid4())
        rand_ticker = f"SYM_{random.randint(100, 999)}"
        rand_volume = round(random.uniform(50.0, 500.0), 2)
        rand_volatility = round(random.uniform(0.2, 0.8), 4)

        params = OrderExecutionParameters(
            order_id=rand_order_id,
            ticker=rand_ticker,
            volume=rand_volume,
            volatility=rand_volatility
        )

        impact = self.model.estimate_market_impact(params)
        self.assertIsInstance(impact, float)
        self.assertGreater(impact, 0.0)
        self.assertEqual(len(self.alert_dispatcher.dispatched), 1)
        self.assertEqual(self.alert_dispatcher.dispatched[0].get("multiplier"), 1.5)

    def test_simulate_stress_slippage_integration(self):
        rand_ticker = f"STRESS_{random.randint(10, 99)}"
        rand_volume = round(random.uniform(100.0, 1000.0), 2)
        scenario_name = f"scenario_{uuid.uuid4()}"

        result = self.model.simulate_stress_slippage(rand_ticker, rand_volume, scenario_name)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("scenario"), scenario_name)
        self.assertEqual(result.get("stress_multiplier"), 2.2)
        self.assertIn("adjusted_slippage", result)
        self.assertGreater(result["adjusted_slippage"], 0.0)

    def test_simulate_order_execution_and_persistence_integration(self):
        sim_id = str(uuid.uuid4())
        order_id = str(uuid.uuid4())
        symbol = f"ASSET_{random.randint(1000, 9999)}"
        quantity = random.randint(100, 5000)
        price = round(random.uniform(10.0, 200.0), 2)

        order_data = {
            "order_id": order_id,
            "symbol": symbol,
            "side": "BUY",
            "quantity": quantity,
            "price": price
        }
        market_context = {
            "adv": 500000,
            "volatility": 0.25,
            "spread_bps": 4.0
        }

        execution_res = self.model.simulate_order_execution(order_data, market_context)
        self.assertEqual(execution_res.get("order_id"), order_id)
        self.assertEqual(execution_res.get("symbol"), symbol)
        self.assertEqual(execution_res.get("status"), "FILLED")

        batch_result = [execution_res]
        persist_success = self.model.persist_execution_logs(sim_id, batch_result, self.db_storage)
        self.assertTrue(persist_success)

        fetched_logs = self.model.get_execution_logs(sim_id, self.db_storage)
        self.assertEqual(len(fetched_logs), 1)
        self.assertEqual(fetched_logs[0].get("order_id"), order_id)

    def test_calculate_slippage_invalid_parameters_raises(self):
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