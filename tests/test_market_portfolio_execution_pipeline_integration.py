import unittest
import os
import uuid
import random
from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline, ExecutionPipelineError

class TestMarketPortfolioExecutionPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"test_execution_storage_{uuid.uuid4().hex}.json"
        self.pipeline = MarketPortfolioExecutionPipeline(storage_file=self.storage_file)

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_simulate_execution_integration(self):
        symbol = f"TICK_{uuid.uuid4().hex[:4].upper()}"
        volume = round(random.uniform(10.0, 1000.0), 2)
        price = round(random.uniform(50.0, 500.0), 2)
        order_type = random.choice(["BUY", "SELL"])
        percentage_shift = round(random.uniform(-0.1, 0.1), 4)

        result = self.pipeline.simulate_execution(
            symbol=symbol,
            volume=volume,
            price=price,
            order_type=order_type,
            percentage_shift=percentage_shift
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("symbol"), symbol)
        self.assertIn("simulation_id", result)
        self.assertIn("slippage", result)
        self.assertIn("scenario_result", result)
        self.assertIn("executed_price", result)
        self.assertIsInstance(result.get("executed_price"), float)

    def test_run_stress_execution_integration(self):
        symbol = f"STRESS_{uuid.uuid4().hex[:4].upper()}"
        volume = round(random.uniform(100.0, 5000.0), 2)
        shifts = [round(random.uniform(-0.2, -0.05), 2), round(random.uniform(0.05, 0.2), 2)]

        result = self.pipeline.run_stress_execution(
            symbol=symbol,
            volume=volume,
            shifts=shifts
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("symbol"), symbol)
        evaluations = result.get("stress_evaluations")
        self.assertIsInstance(evaluations, list)
        self.assertEqual(len(evaluations), len(shifts))

        for eval_item in evaluations:
            self.assertIn("shift_percentage", eval_item)
            self.assertIn("slippage", eval_item)
            self.assertIn("scenario_outcome", eval_item)
            self.assertIn(eval_item["shift_percentage"], shifts)

    def test_execute_order_simulation_integration(self):
        ticker = f"ORD_{uuid.uuid4().hex[:4].upper()}"
        order_data = {
            "ticker": ticker,
            "volume": round(random.uniform(1.0, 100.0), 2),
            "price": round(random.uniform(10.0, 100.0), 2),
            "order_type": "BUY"
        }
        market_context = {"price": order_data["price"]}
        percentage = round(random.uniform(-0.05, 0.05), 4)

        result = self.pipeline.execute_order_simulation(order_data, market_context, percentage)

        self.assertIsInstance(result, dict)
        self.assertIn("scenario_result", result)
        self.assertIn("execution_result", result)

    def test_run_stress_pipeline_integration(self):
        ticker = f"STR_{uuid.uuid4().hex[:4].upper()}"
        shifts = [round(random.uniform(-0.15, -0.01), 2)]
        volume = round(random.uniform(50.0, 500.0), 2)
        scenario_name = f"scenario_{uuid.uuid4().hex[:6]}"

        result = self.pipeline.run_stress_pipeline(ticker, shifts, volume, scenario_name)

        self.assertIsInstance(result, dict)
        self.assertIn("stress_scenario", result)
        self.assertIn("stress_slippage", result)

if __name__ == "__main__":
    unittest.main()