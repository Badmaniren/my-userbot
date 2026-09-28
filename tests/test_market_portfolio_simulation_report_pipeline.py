import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_simulation_report_pipeline import (
    MarketPortfolioSimulationReportPipeline,
    SimulationReportPipelineError
)


class TestMarketPortfolioSimulationReportPipeline(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.pipeline = MarketPortfolioSimulationReportPipeline(storage_file=self.storage_file)

    def test_init_sets_storage_file(self):
        rand_storage = f"{uuid.uuid4().hex}.db"
        pipe = MarketPortfolioSimulationReportPipeline(storage_file=rand_storage)
        self.assertEqual(pipe.storage_file, rand_storage)
        self.assertIsNotNone(pipe.simulator)
        self.assertIsNotNone(pipe.execution_pipeline)

    @patch('skills.market_portfolio_simulation_report_pipeline.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_simulation_report_pipeline.MarketPortfolioExecutionPipeline')
    def test_generate_simulation_report_success(self, mock_exec_cls, mock_sim_cls):
        mock_sim_instance = mock_sim_cls.return_value
        mock_exec_instance = mock_exec_cls.return_value

        pipeline = MarketPortfolioSimulationReportPipeline(storage_file=self.storage_file)

        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        rand_percentage = random.uniform(1.0, 20.0)
        rand_slippage = random.uniform(0.001, 0.05)

        sim_result_data = {
            "symbol": rand_symbol,
            "percentage": rand_percentage,
            "simulated_value": random.uniform(100, 1000)
        }
        mock_sim_instance.simulate_scenario.return_value = sim_result_data

        order_data = {
            "symbol": rand_symbol,
            "volume": random.randint(10, 500),
            "price": random.uniform(10.0, 200.0),
            "order_type": random.choice(["BUY", "SELL"])
        }
        market_context = {"trend": random.choice(["BULL", "BEAR"]), "volatility": random.uniform(0.1, 0.9)}

        exec_result_data = {
            "execution_id": uuid.uuid4().hex,
            "status": "EXECUTED",
            "filled_price": order_data["price"] * (1 + rand_slippage)
        }
        mock_exec_instance.execute_order_simulation.return_value = exec_result_data

        report = pipeline.generate_simulation_report(
            symbol=rand_symbol,
            percentage=rand_percentage,
            slippage_factor=rand_slippage,
            order_data=order_data,
            market_context=market_context
        )

        mock_sim_instance.simulate_scenario.assert_called_once_with(
            symbol=rand_symbol,
            percentage=rand_percentage,
            slippage_factor=rand_slippage
        )
        mock_exec_instance.execute_order_simulation.assert_called_once_with(
            order_data=order_data,
            market_context=market_context,
            percentage=rand_percentage
        )

        self.assertIn("report_id", report)
        self.assertEqual(report["symbol"], rand_symbol)
        self.assertEqual(report["scenario_simulation"], sim_result_data)
        self.assertEqual(report["execution_simulation"], exec_result_data)

    @patch('skills.market_portfolio_simulation_report_pipeline.PortfolioScenarioSimulator')
    def test_generate_simulation_report_scenario_error(self, mock_sim_cls):
        mock_sim_instance = mock_sim_cls.return_value
        rand_msg = uuid.uuid4().hex
        mock_sim_instance.simulate_scenario.side_effect = Exception(rand_msg)

        pipeline = MarketPortfolioSimulationReportPipeline(storage_file=self.storage_file)

        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=3))
        rand_percentage = random.uniform(1.0, 10.0)
        rand_slippage = random.uniform(0.01, 0.05)
        order_data = {"symbol": rand_symbol}
        market_context = {}

        with self.assertRaises(SimulationReportPipelineError) as ctx:
            pipeline.generate_simulation_report(
                symbol=rand_symbol,
                percentage=rand_percentage,
                slippage_factor=rand_slippage,
                order_data=order_data,
                market_context=market_context
            )
        self.assertIn(rand_msg, str(ctx.exception))

    @patch('skills.market_portfolio_simulation_report_pipeline.PortfolioScenarioSimulator')
    @patch('skills.market_portfolio_simulation_report_pipeline.MarketPortfolioExecutionPipeline')
    def test_run_batch_report_pipeline(self, mock_exec_cls, mock_sim_cls):
        mock_sim_instance = mock_sim_cls.return_value
        mock_exec_instance = mock_exec_cls.return_value

        pipeline = MarketPortfolioSimulationReportPipeline(storage_file=self.storage_file)

        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        rand_shifts = [random.uniform(-5.0, 5.0) for _ in range(3)]
        rand_volume = random.randint(100, 1000)
        rand_scenario = uuid.uuid4().hex

        stress_sim_result = {
            "scenario": rand_scenario,
            "shifts_tested": rand_shifts,
            "outcome": uuid.uuid4().hex
        }
        stress_exec_result = {
            "ticker": rand_symbol,
            "status": "STRESS_PASSED"
        }

        mock_sim_instance.run_stress_test.return_value = stress_sim_result
        mock_exec_instance.run_stress_pipeline.return_value = stress_exec_result

        batch_report = pipeline.run_batch_report_pipeline(
            ticker=rand_symbol,
            shifts=rand_shifts,
            volume=rand_volume,
            scenario_name=rand_scenario
        )

        mock_sim_instance.run_stress_test.assert_called_once_with(
            symbol=rand_symbol,
            shifts=rand_shifts
        )
        mock_exec_instance.run_stress_pipeline.assert_called_once_with(
            ticker=rand_symbol,
            shifts=rand_shifts,
            volume=rand_volume,
            scenario_name=rand_scenario
        )

        self.assertIn("batch_id", batch_report)
        self.assertEqual(batch_report["ticker"], rand_symbol)
        self.assertEqual(batch_report["stress_simulation"], stress_sim_result)
        self.assertEqual(batch_report["stress_execution"], stress_exec_result)

    @patch('skills.market_portfolio_simulation_report_pipeline.MarketPortfolioExecutionPipeline')
    def test_run_batch_report_pipeline_execution_error(self, mock_exec_cls):
        mock_exec_instance = mock_exec_cls.return_value
        rand_error_text = uuid.uuid4().hex
        mock_exec_instance.run_stress_pipeline.side_effect = RuntimeError(rand_error_text)

        pipeline = MarketPortfolioSimulationReportPipeline(storage_file=self.storage_file)

        rand_symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        rand_shifts = [1.0, 2.0]
        rand_volume = 50
        rand_scenario = uuid.uuid4().hex

        with self.assertRaises(SimulationReportPipelineError) as ctx:
            pipeline.run_batch_report_pipeline(
                ticker=rand_symbol,
                shifts=rand_shifts,
                volume=rand_volume,
                scenario_name=rand_scenario
            )
        self.assertIn(rand_error_text, str(ctx.exception))
