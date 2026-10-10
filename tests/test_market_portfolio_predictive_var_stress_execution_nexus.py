import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_predictive_var_hedge_synthesizer import PredictiveVarHedgeSynthesizer
from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline, ExecutionPipelineError
from skills.market_portfolio_predictive_var_stress_execution_nexus import (
    PredictiveVarStressExecutionNexus,
    NexusExecutionError
)

class TestMarketPortfolioPredictiveVarStressExecutionNexus(unittest.TestCase):
    def setUp(self):
        self.db_storage_path = f"/tmp/{uuid.uuid4().hex}.db"
        self.nexus = PredictiveVarStressExecutionNexus(db_storage=self.db_storage_path)
        self.portfolio_id = uuid.uuid4().hex
        self.request_id = uuid.uuid4().hex
        self.scenario_code = f"SCENARIO_{uuid.uuid4().hex[:8].upper()}"
        self.symbol = "".join(random.choices(string.ascii_uppercase, k=4))
        self.volume = random.randint(100, 10000)
        self.portfolio_value = round(random.uniform(50000.0, 1000000.0), 2)
        self.percentage = round(random.uniform(1.0, 20.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(3)]
        self.simulations = random.randint(100, 1000)
        self.horizon_days = random.randint(1, 30)
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.scenario_params = {"volatility": round(random.uniform(0.1, 0.5), 2)}
        self.iterations = random.randint(50, 500)

    def test_nexus_initialization(self):
        self.assertIsInstance(self.nexus.synthesizer, PredictiveVarHedgeSynthesizer)
        self.assertIsInstance(self.nexus.execution_pipeline, MarketPortfolioExecutionPipeline)
        self.assertEqual(self.nexus.storage_file, self.db_storage_path)

    def test_synthesize_var_and_execute_success(self):
        expected_synthesis = {
            "status": "success",
            "request_id": self.request_id,
            "hedge_action": "BUY",
            "volume": self.volume
        }
        expected_execution = {
            "execution_id": uuid.uuid4().hex,
            "status": "executed",
            "symbol": self.symbol,
            "volume": self.volume
        }

        with patch.object(PredictiveVarHedgeSynthesizer, 'synthesize_and_execute_hedge', return_value=expected_synthesis) as mock_synth, \
             patch.object(MarketPortfolioExecutionPipeline, 'simulate_execution', return_value=expected_execution) as mock_exec:

            result = self.nexus.synthesize_var_and_execute(
                portfolio_id=self.portfolio_id,
                scenario_code=self.scenario_code,
                simulations=self.simulations,
                horizon_days=self.horizon_days,
                confidence_level=self.confidence_level,
                portfolio_value=self.portfolio_value,
                scenario_params=self.scenario_params,
                iterations=self.iterations,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts
            )

            mock_synth.assert_called_once()
            mock_exec.assert_called_once()
            self.assertIn("synthesis", result)
            self.assertIn("execution", result)
            self.assertEqual(result["synthesis"]["request_id"], self.request_id)
            self.assertEqual(result["execution"]["symbol"], self.symbol)

    def test_synthesize_var_and_execute_failure_handling(self):
        with patch.object(PredictiveVarHedgeSynthesizer, 'synthesize_and_execute_hedge', side_effect=Exception("Var Synthesizer Failure")):
            with self.assertRaises(NexusExecutionError) as ctx:
                self.nexus.synthesize_var_and_execute(
                    portfolio_id=self.portfolio_id,
                    scenario_code=self.scenario_code,
                    simulations=self.simulations,
                    horizon_days=self.horizon_days,
                    confidence_level=self.confidence_level,
                    portfolio_value=self.portfolio_value,
                    scenario_params=self.scenario_params,
                    iterations=self.iterations,
                    request_id=self.request_id,
                    symbol=self.symbol,
                    percentage=self.percentage,
                    shifts=self.shifts
                )
            self.assertIn("Var Synthesizer Failure", str(ctx.exception))

    def test_run_stress_var_pipeline_nexus(self):
        expected_stress_result = {
            "stress_scenario": self.scenario_code,
            "ticker": self.symbol,
            "max_drawdown": round(random.uniform(-0.5, -0.1), 4)
        }

        with patch.object(MarketPortfolioExecutionPipeline, 'run_stress_pipeline', return_value=expected_stress_result) as mock_stress:
            res = self.nexus.run_stress_var_pipeline_nexus(
                ticker=self.symbol,
                shifts=self.shifts,
                volume=self.volume,
                scenario_name=self.scenario_code
            )

            mock_stress.assert_called_once_with(self.symbol, self.shifts, self.volume, self.scenario_code)
            self.assertEqual(res["stress_scenario"], self.scenario_code)
            self.assertEqual(res["ticker"], self.symbol)

    def test_process_stream_auto_hedge_and_execute(self):
        stream_mock = io.BytesIO(uuid.uuid4().bytes)
        expected_stream_result = {
            "processed": True,
            "auto_hedge_triggered": True,
            "request_id": self.request_id
        }

        with patch.object(PredictiveVarHedgeSynthesizer, 'process_stream_and_auto_hedge', return_value=expected_stream_result) as mock_stream, \
             patch.object(MarketPortfolioExecutionPipeline, 'run_stress_execution', return_value={"status": "completed"}) as mock_run_stress:

            response = self.nexus.process_stream_auto_hedge_and_execute(
                stream_mock=stream_mock,
                portfolio_id=self.portfolio_id,
                request_id=self.request_id,
                symbol=self.symbol,
                percentage=self.percentage,
                shifts=self.shifts,
                volume=self.volume
            )

            mock_stream.assert_called_once()
            mock_run_stress.assert_called_once_with(self.symbol, self.volume, self.shifts)
            self.assertTrue(response["stream_result"]["processed"])
            self.assertEqual(response["execution_status"]["status"], "completed")

    def test_pipeline_error_propagation_in_nexus(self):
        with patch.object(MarketPortfolioExecutionPipeline, 'simulate_execution', side_effect=ExecutionPipelineError("Pipeline dropped order")):
            with patch.object(PredictiveVarHedgeSynthesizer, 'synthesize_and_execute_hedge', return_value={"status": "ok"}):
                with self.assertRaises(NexusExecutionError) as ctx:
                    self.nexus.synthesize_var_and_execute(
                        portfolio_id=self.portfolio_id,
                        scenario_code=self.scenario_code,
                        simulations=self.simulations,
                        horizon_days=self.horizon_days,
                        confidence_level=self.confidence_level,
                        portfolio_value=self.portfolio_value,
                        scenario_params=self.scenario_params,
                        iterations=self.iterations,
                        request_id=self.request_id,
                        symbol=self.symbol,
                        percentage=self.percentage,
                        shifts=self.shifts
                    )
                self.assertIn("Pipeline dropped order", str(ctx.exception))

if __name__ == '__main__':
    unittest.main()