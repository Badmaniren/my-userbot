import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

from skills.market_portfolio_predictive_var_hedge_synthesizer import PredictiveVarHedgeSynthesizer, VarEngineError, InsufficientDataError


class TestPredictiveVarHedgeSynthesizer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.request_id = str(uuid.uuid4())
        self.scenario_code = ''.join(random.choices(string.ascii_uppercase, k=6))
        self.symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        self.simulations = random.randint(1000, 10000)
        self.horizon_days = random.randint(1, 30)
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        self.iterations = random.randint(50, 500)
        self.percentage = round(random.uniform(1.0, 25.0), 2)
        self.shifts = [round(random.uniform(-0.1, 0.1), 4) for _ in range(random.randint(3, 8))]
        self.scenario_params = {"param_key": ''.join(random.choices(string.ascii_lowercase, k=5))}

        self.mock_var_engine = MagicMock()
        self.mock_auto_hedge_sync = MagicMock()

        self.synthesizer = PredictiveVarHedgeSynthesizer(
            var_engine=self.mock_var_engine,
            auto_hedge_sync=self.mock_auto_hedge_sync
        )

    def test_synthesize_and_execute_hedge_success(self):
        expected_var_metrics = {
            "portfolio_id": self.portfolio_id,
            "predictive_var": round(random.uniform(100.0, 5000.0), 2)
        }
        expected_hedge_result = {
            "portfolio_id": self.portfolio_id,
            "status": "SYNCHRONIZED",
            "symbol": self.symbol
        }

        self.mock_var_engine.calculate_predictive_var.return_value = expected_var_metrics
        self.mock_auto_hedge_sync.synchronize.return_value = expected_hedge_result

        result = self.synthesizer.synthesize_and_execute_hedge(
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

        self.mock_var_engine.calculate_predictive_var.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            scenario_code=self.scenario_code,
            simulations=self.simulations,
            horizon_days=self.horizon_days,
            confidence_level=self.confidence_level,
            portfolio_value=self.portfolio_value,
            scenario_params=self.scenario_params,
            iterations=self.iterations
        )

        self.mock_auto_hedge_sync.synchronize.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["var_metrics"], expected_var_metrics)
        self.assertEqual(result["hedge_result"], expected_hedge_result)

    def test_synthesize_stress_var_and_hedge_success(self):
        expected_stress_var = {
            "portfolio_id": self.portfolio_id,
            "stress_var": round(random.uniform(500.0, 10000.0), 2)
        }
        expected_hedge_result = {
            "portfolio_id": self.portfolio_id,
            "status": "EXECUTED"
        }

        self.mock_var_engine.calculate_predictive_stress_var.return_value = expected_stress_var
        self.mock_auto_hedge_sync.synchronize.return_value = expected_hedge_result

        result = self.synthesizer.synthesize_stress_var_and_hedge(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.portfolio_value,
            scenario_params=self.scenario_params,
            confidence_level=self.confidence_level,
            horizon_days=self.horizon_days,
            iterations=self.iterations,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.mock_var_engine.calculate_predictive_stress_var.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            portfolio_value=self.portfolio_value,
            scenario_params=self.scenario_params,
            confidence_level=self.confidence_level,
            horizon_days=self.horizon_days,
            iterations=self.iterations
        )

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["stress_var_metrics"], expected_stress_var)
        self.assertEqual(result["hedge_result"], expected_hedge_result)

    def test_process_stream_and_auto_hedge_success(self):
        stream_mock = io.BytesIO(uuid.uuid4().bytes)
        expected_stream_response = {"status": "STREAM_PROCESSED"}
        expected_hedge_result = {"status": "SYNC_OK"}

        self.mock_var_engine.process_market_stream.return_value = expected_stream_response
        self.mock_auto_hedge_sync.synchronize.return_value = expected_hedge_result

        result = self.synthesizer.process_stream_and_auto_hedge(
            stream_mock=stream_mock,
            portfolio_id=self.portfolio_id,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            shifts=self.shifts
        )

        self.mock_var_engine.process_market_stream.assert_called_once_with(stream_mock)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["stream_response"], expected_stream_response)
        self.assertEqual(result["hedge_result"], expected_hedge_result)

    def test_synthesize_and_simulate_exception_fallback(self):
        self.mock_var_engine.calculate_predictive_var.side_effect = InsufficientDataError(uuid.uuid4().hex)
        expected_hedge_result = {"status": "FALLBACK_SYNC"}

        self.mock_auto_hedge_sync.synchronize.return_value = expected_hedge_result

        result = self.synthesizer.synthesize_and_simulate(
            portfolio_id=self.portfolio_id,
            scenario_code=self.scenario_code,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            portfolio_value=self.portfolio_value,
            simulations=self.simulations,
            horizon_days=self.horizon_days,
            confidence_level=self.confidence_level,
            scenario_params=self.scenario_params,
            iterations=self.iterations,
            shifts=self.shifts
        )

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["var_metrics"]["predictive_var"], 0.0)
        self.assertEqual(result["var_metrics"]["confidence"], self.confidence_level)
        self.assertEqual(result["var_metrics"]["scenario_code"], self.scenario_code)
        self.assertEqual(result["hedge_status"], "FALLBACK_SYNC")

    def test_synthesize_and_simulate_no_status_in_hedge(self):
        expected_var_metrics = {"predictive_var": random.uniform(10.0, 100.0)}
        self.mock_var_engine.calculate_predictive_var.return_value = expected_var_metrics
        self.mock_auto_hedge_sync.synchronize.return_value = ["not_a_dict"]

        result = self.synthesizer.synthesize_and_simulate(
            portfolio_id=self.portfolio_id,
            scenario_code=self.scenario_code,
            request_id=self.request_id,
            symbol=self.symbol,
            percentage=self.percentage,
            portfolio_value=self.portfolio_value,
            simulations=self.simulations,
            horizon_days=self.horizon_days,
            confidence_level=self.confidence_level,
            scenario_params=self.scenario_params,
            iterations=self.iterations,
            shifts=self.shifts
        )

        self.assertEqual(result["hedge_status"], "SYNCHRONIZED")


if __name__ == "__main__":
    unittest.main()