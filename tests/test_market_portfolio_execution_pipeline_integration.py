import json
import os
import random
import tempfile
import unittest
import uuid

from skills.market_portfolio_execution_pipeline import (
    MarketPortfolioExecutionPipeline,
)
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_portfolio_slippage_model import MarketPortfolioSlippageModel


class TestMarketPortfolioExecutionPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(
            self.temp_dir.name, f"portfolio_{uuid.uuid4().hex}.json"
        )
        self.unique_id = uuid.uuid4().hex[:6].upper()
        self.ticker = f"TEST_{self.unique_id}"
        self.initial_qty = random.randint(50, 200)
        self.initial_price = round(random.uniform(70.0, 250.0), 2)

        # Подготовка универсальной структуры портфеля для реального PortfolioScenarioSimulator
        self.portfolio_data = {
            "portfolio": [
                {
                    "symbol": self.ticker,
                    "shares": self.initial_qty,
                    "quantity": self.initial_qty,
                    "current_price": self.initial_price,
                    "price": self.initial_price,
                }
            ],
            "positions": {
                self.ticker: {
                    "quantity": self.initial_qty,
                    "current_price": self.initial_price,
                    "price": self.initial_price,
                }
            },
            self.ticker: {
                "shares": self.initial_qty,
                "quantity": self.initial_qty,
                "current_price": self.initial_price,
                "price": self.initial_price,
            },
        }

        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(self.portfolio_data, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pipeline_composition_initialization(self):
        pipeline = MarketPortfolioExecutionPipeline(
            storage_file=self.storage_file
        )
        self.assertIsInstance(
            pipeline.slippage_model, MarketPortfolioSlippageModel
        )
        self.assertIsInstance(
            pipeline.scenario_simulator, PortfolioScenarioSimulator
        )

    def test_simulate_order_execution_end_to_end(self):
        pipeline = MarketPortfolioExecutionPipeline(
            storage_file=self.storage_file
        )

        test_volume = random.randint(5, 30)
        test_price = self.initial_price
        test_shift_pct = round(random.uniform(-8.0, 8.0), 2)
        test_order_type = random.choice(["BUY", "SELL"])

        result = pipeline.simulate_execution(
            symbol=self.ticker,
            volume=test_volume,
            price=test_price,
            order_type=test_order_type,
            percentage_shift=test_shift_pct,
        )

        self.assertIsInstance(result, dict)
        self.assertIn("simulation_id", result)
        self.assertIn("symbol", result)
        self.assertEqual(result["symbol"], self.ticker)

        self.assertIn("slippage", result)
        self.assertIsInstance(result["slippage"], (int, float))
        self.assertGreaterEqual(result["slippage"], 0.0)

        self.assertIn("scenario_result", result)
        self.assertIsInstance(result["scenario_result"], dict)

        self.assertIn("executed_price", result)
        self.assertIsInstance(result["executed_price"], (int, float))
        self.assertGreater(result["executed_price"], 0.0)

        if test_order_type == "BUY" and result["slippage"] > 0:
            self.assertGreaterEqual(result["executed_price"], test_price)

    def test_stress_execution_pipeline(self):
        pipeline = MarketPortfolioExecutionPipeline(
            storage_file=self.storage_file
        )

        test_volume = random.randint(10, 40)
        shifts = [-10.0, -5.0, 0.0, 5.0, 10.0]

        stress_results = pipeline.run_stress_execution(
            symbol=self.ticker,
            volume=test_volume,
            shifts=shifts,
        )

        self.assertIsInstance(stress_results, dict)
        self.assertIn("symbol", stress_results)
        self.assertEqual(stress_results["symbol"], self.ticker)
        self.assertIn("stress_evaluations", stress_results)

        evaluations = stress_results["stress_evaluations"]
        self.assertEqual(len(evaluations), len(shifts))

        for item in evaluations:
            self.assertIn("shift_percentage", item)
            self.assertIn(item["shift_percentage"], shifts)
            self.assertIn("slippage", item)
            self.assertIn("scenario_outcome", item)


if __name__ == "__main__":
    unittest.main()