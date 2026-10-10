import unittest
from unittest.mock import MagicMock, patch
import random
import uuid
import string

from skills.market_portfolio_predictive_var_hedge_synthesizer import (
    PredictiveVarHedgeSynthesizer,
    MarketPortfolioPredictiveVarHedgeSynthesizer
)


class TestPredictiveVarHedgeSynthesizer(unittest.TestCase):

    def setUp(self):
        self.rand_portfolio_id = str(uuid.uuid4())
        self.rand_scenario_code = "".join(random.choices(string.ascii_uppercase, k=8))
        self.rand_request_id = str(uuid.uuid4())
        self.rand_symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        
        self.rand_simulations = random.randint(100, 10000)
        self.rand_horizon_days = random.randint(1, 30)
        self.rand_confidence = round(random.uniform(0.90, 0.99), 4)
        self.rand_portfolio_value = round(random.uniform(10000.0, 1000000.0), 2)
        self.rand_iterations = random.randint(10, 500)
        self.rand_percentage = round(random.uniform(-10.0, 150.0), 2)
        self.rand_shifts = [round(random.uniform(-0.05, 0.05), 4) for _ in range(3)]
        self.rand_scenario_params = {
            "".join(random.choices(string.ascii_lowercase, k=5)): random.random()
            for _ in range(3)
        }

        self.mock_var_engine = MagicMock()
        self.mock_auto_hedge_sync = MagicMock()

        self.synthesizer = PredictiveVarHedgeSynthesizer(
            var_engine=self.mock_var_engine,
            auto_hedge_sync=self.mock_auto_hedge_sync
        )

    def test_alias_existence(self):
        self.assertIs(MarketPortfolioPredictiveVarHedgeSynthesizer, PredictiveVarHedgeSynthesizer)

    def test_normalize_percentage_boundary_and_types(self):
        self.assertEqual(self.synthesizer._normalize_percentage(None), 0.0)
        self.assertEqual(self.synthesizer._normalize_percentage(-50.0), 0.0)
        self.assertEqual(self.synthesizer._normalize_percentage(150.0), 100.0)
        self.assertEqual(self.synthesizer._normalize_percentage("invalid_str"), 0.0)
        
        rand_valid = round(random.uniform(0.0, 100.0), 2)
        self.assertEqual(self.synthesizer._normalize_percentage(rand_valid), rand_valid)

    def test_synthesize_and_execute_hedge_success(self):
        expected_var_result = {
            "portfolio_id": self.rand_portfolio_id,
            "predictive_var": round(random.uniform(100.0, 5000.0), 2),
            "confidence": self.rand_confidence,
            "scenario_code": self.rand_scenario_code
        }
        expected_hedge_result = {
            "status": "SYNCHRONIZED",
            "execution_id": str(uuid.uuid4())
        }

        self.mock_var_engine.calculate_predictive_var.return_value = expected_var_result
        self.mock_auto_hedge_sync.synchronize.return_value = expected_hedge_result

        result = self.synthesizer.synthesize_and_execute_hedge(
            portfolio_id=self.rand_portfolio_id,
            scenario_code=self.rand_scenario_code,
            simulations=self.rand_simulations,
            horizon_days=self.rand_horizon_days,
            confidence_level=self.rand_confidence,
            portfolio_value=self.rand_portfolio_value,
            scenario_params=self.rand_scenario_params,
            iterations=self.rand_iterations,
            request_id=self.rand_request_id,
            symbol=self.rand_symbol,
            percentage=self.rand_percentage,
            shifts=self.rand_shifts
        )

        self.assertEqual(result["portfolio_id"], self.rand_portfolio_id)
        self.assertEqual(result["var_metrics"], expected_var_result)
        self.assertEqual(result["hedge_result"], expected_hedge_result)
        
        normalized_expected = max(0.0, min(100.0, float(self.rand_percentage)))
        self.mock_auto_hedge_sync.synchronize.assert_called_once_with(
            portfolio_id=self.rand_portfolio_id,
            request_id=self.rand_request_id,
            symbol=self.rand_symbol,
            percentage=normalized_expected,
            shifts=self.rand_shifts
        )

    def test_synthesize_and_execute_hedge_exception_fallback(self):
        self.mock_var_engine.calculate_predictive_var.side_effect = Exception("Engine failure")
        expected_hedge_result = {"status": "FAILED"}
        self.mock_auto_hedge_sync.synchronize.return_value = expected_hedge_result

        result = self.synthesizer.synthesize_and_execute_hedge(
            portfolio_id=self.rand_portfolio_id,
            scenario_code=self.rand_scenario_code,
            simulations=self.rand_simulations,
            horizon_days=self.rand_horizon_days,
            confidence_level=self.rand_confidence,
            portfolio_value=self.rand_portfolio_value,
            scenario_params=self.rand_scenario_params,
            iterations=self.rand_iterations,
            request_id=self.rand_request_id,
            symbol=self.rand_symbol,
            percentage=self.rand_percentage,
            shifts=self.rand_shifts
        )

        self.assertEqual(result["portfolio_id"], self.rand_portfolio_id)
        self.assertEqual(result["var_metrics"]["predictive_var"], 0.0)
        self.assertEqual(result["var_metrics"]["confidence"], self.rand_confidence)
        self.assertEqual(result["var_metrics"]["scenario_code"], self.rand_scenario_code)
        self.assertEqual(result["hedge_result"], expected_hedge_result)

    def test_synthesize_stress_var_and_hedge(self):
        expected_stress_var = {
            "portfolio_id": self.rand_portfolio_id,
            "stress_var": round(random.uniform(500.0, 10000.0), 2)
        }
        expected_hedge_result = {"status": "HEDGED"}

        self.mock_var_engine.calculate_predictive_stress_var.return_value = expected_stress_var
        self.mock_auto_hedge_sync.synchronize.return_value = expected_hedge_result

        result = self.synthesizer.synthesize_stress_var_and_hedge(
            portfolio_id=self.rand_portfolio_id,
            portfolio_value=self.rand_portfolio_value,
            scenario_params=self.rand_scenario_params,
            confidence_level=self.rand_confidence,
            horizon_days=self.rand_horizon_days,
            iterations=self.rand_iterations,
            request_id=self.rand_request_id,
            symbol=self.rand_symbol,
            percentage=self.rand_percentage,
            shifts=self.rand_shifts
        )

        self.assertEqual(result["portfolio_id"], self.rand_portfolio_id)
        self.assertEqual(result["stress_var_metrics"], expected_stress_var)
        self.assertEqual(result["hedge_result"], expected_hedge_result)

    def test_process_stream_and_auto_hedge(self):
        stream_mock_obj = MagicMock()
        expected_stream_response = {"stream_status": "PROCESSED", "id": str(uuid.uuid4())}
        expected_hedge_result = {"status": "STREAM_HEDGED"}

        self.mock_var_engine.process_market_stream.return_value = expected_stream_response
        self.mock_auto_hedge_sync.synchronize.return_value = expected_hedge_result

        result = self.synthesizer.process_stream_and_auto_hedge(
            stream_mock=stream_mock_obj,
            portfolio_id=self.rand_portfolio_id,
            request_id=self.rand_request_id,
            symbol=self.rand_symbol,
            percentage=self.rand_percentage,
            shifts=self.rand_shifts
        )

        self.assertEqual(result["portfolio_id"], self.rand_portfolio_id)
        self.assertEqual(result["stream_response"], expected_stream_response)
        self.assertEqual(result["hedge_result"], expected_hedge_result)
        self.mock_var_engine.process_market_stream.assert_called_once_with(stream_mock_obj)

    def test_synthesize_and_simulate_with_custom_status(self):
        expected_var_result = {
            "portfolio_id": self.rand_portfolio_id,
            "predictive_var": round(random.uniform(50.0, 1500.0), 2)
        }
        rand_custom_status = "".join(random.choices(string.ascii_uppercase, k=10))
        expected_hedge_result = {
            "status": rand_custom_status,
            "data": str(uuid.uuid4())
        }

        self.mock_var_engine.calculate_predictive_var.return_value = expected_var_result
        self.mock_auto_hedge_sync.synchronize.return_value = expected_hedge_result

        result = self.synthesizer.synthesize_and_simulate(
            portfolio_id=self.rand_portfolio_id,
            scenario_code=self.rand_scenario_code,
            request_id=self.rand_request_id,
            symbol=self.rand_symbol,
            percentage=self.rand_percentage,
            portfolio_value=self.rand_portfolio_value,
            simulations=self.rand_simulations,
            horizon_days=self.rand_horizon_days,
            confidence_level=self.rand_confidence,
            scenario_params=self.rand_scenario_params,
            iterations=self.rand_iterations,
            shifts=self.rand_shifts
        )

        self.assertEqual(result["portfolio_id"], self.rand_portfolio_id)
        self.assertEqual(result["var_metrics"], expected_var_result)
        self.assertEqual(result["hedge_result"], expected_hedge_result)
        self.assertEqual(result["hedge_status"], rand_custom_status)

    def test_synthesize_and_simulate_default_status(self):
        expected_var_result = {"portfolio_id": self.rand_portfolio_id}
        self.mock_var_engine.calculate_predictive_var.return_value = expected_var_result
        self.mock_auto_hedge_sync.synchronize.return_value = "non_dict_hedge_result"

        result = self.synthesizer.synthesize_and_simulate(
            portfolio_id=self.rand_portfolio_id,
            scenario_code=self.rand_scenario_code,
            request_id=self.rand_request_id,
            symbol=self.rand_symbol,
            percentage=self.rand_percentage,
            portfolio_value=self.rand_portfolio_value,
            simulations=self.rand_simulations,
            horizon_days=self.rand_horizon_days,
            confidence_level=self.rand_confidence,
            scenario_params=self.rand_scenario_params,
            iterations=self.rand_iterations,
            shifts=self.rand_shifts
        )

        self.assertEqual(result["hedge_status"], "SYNCHRONIZED")


if __name__ == "__main__":
    unittest.main()