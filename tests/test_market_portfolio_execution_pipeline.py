import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.market_portfolio_execution_pipeline import (
    MarketPortfolioExecutionPipeline,
    ExecutionPipelineError
)

class TestMarketPortfolioExecutionPipeline(unittest.TestCase):
    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.pipeline = MarketPortfolioExecutionPipeline(storage_file=self.storage_file)

    def test_execute_order_simulation_success(self):
        ticker = f"BTC_{uuid.uuid4().hex[:6]}"
        volume = round(random.uniform(1.0, 100.0), 4)
        price = round(random.uniform(100.0, 50000.0), 2)
        percentage = round(random.uniform(-10.0, 10.0), 2)

        order_data = {"ticker": ticker, "volume": volume, "price": price, "order_type": "BUY"}
        market_context = {"price": price, "volatility": random.uniform(0.1, 0.9)}

        mock_scenario_result = {"ticker": ticker, "simulated_change": percentage, "status": "OK"}
        mock_execution_result = {"order_id": uuid.uuid4().hex, "slippage": 0.05, "executed_price": price + 0.05}

        with patch.object(self.pipeline.scenario_simulator, "simulate_scenario", return_value=mock_scenario_result) as mock_sim, \
             patch.object(self.pipeline.slippage_model, "simulate_order_execution", return_value=mock_execution_result) as mock_exec, \
             patch.object(self.pipeline.slippage_model, "persist_execution_logs") as mock_persist:

            result = self.pipeline.execute_order_simulation(order_data, market_context, percentage)

            mock_sim.assert_called_once_with(ticker, percentage)
            mock_exec.assert_called_once_with(order_data, market_context)
            mock_persist.assert_called_once_with(self.storage_file)

            self.assertEqual(result["scenario_result"], mock_scenario_result)
            self.assertEqual(result["execution_result"], mock_execution_result)

    def test_execute_order_simulation_raises_pipeline_error(self):
        ticker = f"ETH_{uuid.uuid4().hex[:6]}"
        percentage = round(random.uniform(-5.0, 5.0), 2)
        order_data = {"ticker": ticker}
        market_context = {}

        with patch.object(self.pipeline.scenario_simulator, "simulate_scenario", side_effect=ValueError("Sim error")):
            with self.assertRaises(ExecutionPipelineError) as ctx:
                self.pipeline.execute_order_simulation(order_data, market_context, percentage)
            self.assertIn("Error in execute_order_simulation", str(ctx.exception))

    def test_run_batch_pipeline_execution_success(self):
        orders = [{"ticker": f"SYM_{uuid.uuid4().hex[:4]}", "volume": random.randint(1, 10)} for _ in range(3)]
        contexts = [{"context_id": uuid.uuid4().hex} for _ in range(3)]
        percentage = round(random.uniform(1.0, 5.0), 2)

        expected_batch = [{"status": "success", "id": uuid.uuid4().hex} for _ in range(3)]

        with patch.object(self.pipeline.slippage_model, "simulate_batch", return_value=expected_batch) as mock_batch, \
             patch.object(self.pipeline.slippage_model, "persist_execution_logs") as mock_persist:

            res = self.pipeline.run_batch_pipeline_execution(orders, contexts, percentage)

            mock_batch.assert_called_once_with(orders, contexts)
            mock_persist.assert_called_once_with(self.storage_file)
            self.assertEqual(res, expected_batch)

    def test_run_batch_pipeline_execution_error(self):
        with patch.object(self.pipeline.slippage_model, "simulate_batch", side_effect=Exception("Batch fail")):
            with self.assertRaises(ExecutionPipelineError):
                self.pipeline.run_batch_pipeline_execution([], [], 1.0)

    def test_run_stress_pipeline_success(self):
        ticker = f"XRP_{uuid.uuid4().hex[:4]}"
        shifts = [random.uniform(-20.0, -10.0), random.uniform(10.0, 20.0)]
        volume = random.uniform(500.0, 1500.0)
        scenario_name = f"stress_test_{uuid.uuid4().hex[:6]}"

        mock_stress_scenario = {"status": "completed", "shifts": shifts}
        mock_stress_slippage = {"slippage_total": random.uniform(1.0, 5.0)}

        with patch.object(self.pipeline.scenario_simulator, "run_stress_test", return_value=mock_stress_scenario) as mock_st, \
             patch.object(self.pipeline.slippage_model, "simulate_stress_slippage", return_value=mock_stress_slippage) as mock_ss:

            res = self.pipeline.run_stress_pipeline(ticker, shifts, volume, scenario_name)

            mock_st.assert_called_once_with(ticker, shifts)
            mock_ss.assert_called_once_with(ticker, volume, scenario_name)
            self.assertEqual(res["stress_scenario"], mock_stress_scenario)
            self.assertEqual(res["stress_slippage"], mock_stress_slippage)

    def test_get_historical_pipeline_logs(self):
        sim_id = uuid.uuid4().hex
        expected_logs = [{"log_id": uuid.uuid4().hex, "details": "sample"}]

        with patch.object(self.pipeline.slippage_model, "get_execution_logs", return_value=expected_logs) as mock_logs:
            res = self.pipeline.get_historical_pipeline_logs(sim_id)
            mock_logs.assert_called_once_with(sim_id, self.storage_file)
            self.assertEqual(res, expected_logs)

    def test_simulate_execution_with_custom_method(self):
        symbol = f"LTC_{uuid.uuid4().hex[:4]}"
        volume = round(random.uniform(10.0, 50.0), 2)
        price = round(random.uniform(50.0, 300.0), 2)
        order_type = random.choice(["BUY", "SELL"])
        percentage_shift = round(random.uniform(-3.0, 3.0), 2)

        sim_id = uuid.uuid4().hex
        slippage_val = 0.12
        scenario_res = {"sim_outcome": "stable"}
        slip_res = {
            "order_id": sim_id,
            "slippage": slippage_val,
            "executed_price": price + slippage_val if order_type == "BUY" else price - slippage_val
        }

        with patch.object(self.pipeline.scenario_simulator, "simulate_scenario", return_value=scenario_res), \
             patch.object(self.pipeline.slippage_model, "simulate_execution", return_value=slip_res, create=True):

            res = self.pipeline.simulate_execution(symbol, volume, price, order_type, percentage_shift)

            self.assertEqual(res["simulation_id"], sim_id)
            self.assertEqual(res["symbol"], symbol)
            self.assertEqual(res["slippage"], slippage_val)
            self.assertEqual(res["scenario_result"], scenario_res)

    def test_run_stress_execution_fallback_slippage(self):
        symbol = f"ADA_{uuid.uuid4().hex[:4]}"
        volume = random.uniform(100.0, 1000.0)
        shifts = [random.uniform(-5.0, 5.0), random.uniform(-10.0, 10.0)]

        with patch.object(self.pipeline.scenario_simulator, "simulate_scenario", return_value={"evaluated": True}) as mock_sim, \
             patch.object(self.pipeline.slippage_model, "simulate_shift_slippage", side_effect=AttributeError, create=True):

            res = self.pipeline.run_stress_execution(symbol, volume, shifts)

            self.assertEqual(res["symbol"], symbol)
            self.assertEqual(len(res["stress_evaluations"]), len(shifts))
            for i, eval_item in enumerate(res["stress_evaluations"]):
                self.assertEqual(eval_item["shift_percentage"], shifts[i])
                self.assertEqual(eval_item["slippage"], 0.5 * abs(shifts[i]))

if __name__ == "__main__":
    unittest.main()