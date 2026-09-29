import unittest
import uuid
import random
from skills.market_portfolio_slippage_model import (
    MarketPortfolioSlippageModel,
    OrderExecutionParameters,
    SlippageCalculationError
)


class RealMarketParser:
    def parse_market_depth(self, ticker: str):
        pass


class RealAnomalyDetector:
    def detect(self, ticker: str):
        return {"multiplier": 1.5}


class RealAlertDispatcher:
    def __init__(self):
        self.dispatched = []

    def dispatch(self, anomaly):
        self.dispatched.append(anomaly)


class RealStressPipeline:
    def run_simulation(self, scenario_name: str):
        return {"stress_multiplier": 2.0}


class RealStorage:
    def __init__(self):
        self.logs = {}

    def save_logs(self, simulation_id: str, executions: list):
        self.logs[simulation_id] = executions

    def get_logs(self, simulation_id: str):
        return self.logs.get(simulation_id, [])


class TestMarketPortfolioSlippageModelIntegration(unittest.TestCase):

    def setUp(self):
        self.market_parser = RealMarketParser()
        self.anomaly_detector = RealAnomalyDetector()
        self.alert_dispatcher = RealAlertDispatcher()
        self.stress_scenario_pipeline = RealStressPipeline()
        self.db_storage = RealStorage()

        self.model = MarketPortfolioSlippageModel(
            market_parser=self.market_parser,
            anomaly_detector=self.anomaly_detector,
            alert_dispatcher=self.alert_dispatcher,
            stress_scenario_pipeline=self.stress_scenario_pipeline,
            db_storage=self.db_storage
        )

    def test_calculate_slippage_integration(self):
        ticker = f"TICK_{uuid.uuid4().hex[:6]}"
        volume = round(random.uniform(1000.0, 50000.0), 2)
        volatility = round(random.uniform(0.1, 0.9), 4)

        params = OrderExecutionParameters(
            order_id=str(uuid.uuid4()),
            ticker=ticker,
            volume=volume,
            volatility=volatility
        )

        result = self.model.calculate_slippage(params)
        expected = round(volume * volatility * 0.0001, 6)
        self.assertEqual(result, expected)

    def test_estimate_market_impact_integration(self):
        ticker = f"TICK_{uuid.uuid4().hex[:6]}"
        volume = round(random.uniform(500.0, 10000.0), 2)
        volatility = round(random.uniform(0.15, 0.5), 4)

        params = OrderExecutionParameters(
            order_id=str(uuid.uuid4()),
            ticker=ticker,
            volume=volume,
            volatility=volatility
        )

        impact = self.model.estimate_market_impact(params)
        expected = float(volume * volatility * 0.00005 * 1.5)
        self.assertEqual(impact, expected)
        self.assertTrue(len(self.alert_dispatcher.dispatched) > 0)

    def test_simulate_stress_slippage_integration(self):
        ticker = f"TICK_{uuid.uuid4().hex[:6]}"
        volume = round(random.uniform(1000.0, 10000.0), 2)
        scenario_name = f"scenario_{uuid.uuid4().hex[:6]}"

        result = self.model.simulate_stress_slippage(ticker, volume, scenario_name)
        self.assertEqual(result["scenario"], scenario_name)
        self.assertEqual(result["stress_multiplier"], 2.0)
        self.assertEqual(result["adjusted_slippage"], round(volume * 0.2 * 0.0001 * 2.0, 6))

    def test_simulate_order_execution_and_persistence(self):
        order_id = str(uuid.uuid4())
        symbol = f"SYM_{uuid.uuid4().hex[:4]}"
        quantity = random.randint(100, 5000)
        price = round(random.uniform(50.0, 500.0), 2)

        order_data = {
            "order_id": order_id,
            "symbol": symbol,
            "side": "BUY",
            "quantity": quantity,
            "price": price
        }
        market_context = {
            "adv": 1000000,
            "volatility": 0.25,
            "spread_bps": 4.0
        }

        execution_result = self.model.simulate_order_execution(order_data, market_context)
        self.assertEqual(execution_result["order_id"], order_id)
        self.assertEqual(execution_result["symbol"], symbol)
        self.assertEqual(execution_result["status"], "FILLED")

        simulation_id = str(uuid.uuid4())
        persisted = self.model.persist_execution_logs(simulation_id, [execution_result], self.db_storage)
        self.assertTrue(persisted)

        fetched_logs = self.model.get_execution_logs(simulation_id, self.db_storage)
        self.assertEqual(len(fetched_logs), 1)
        self.assertEqual(fetched_logs[0]["order_id"], order_id)


if __name__ == "__main__":
    unittest.main()