import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
from skills.market_portfolio_stress_backtest_calibrator import (
    MarketPortfolioStressBacktestCalibrator,
    market_portfolio_stress_backtest_calibrator
)

class TestMarketPortfolioStressBacktestCalibrator(unittest.TestCase):
    def setUp(self):
        self.db_storage_mock = MagicMock()
        self.monte_carlo_engine_mock = MagicMock()
        self.scenario_simulator_mock = MagicMock()

        self.calibrator = MarketPortfolioStressBacktestCalibrator(
            db_storage=self.db_storage_mock,
            market_portfolio_stress_monte_carlo_engine=self.monte_carlo_engine_mock,
            market_portfolio_scenario_simulator=self.scenario_simulator_mock
        )

    def test_calibrate_backtest_success(self):
        portfolio_id = uuid.uuid4().hex
        lookback_days = random.randint(30, 365)
        iterations = random.randint(100, 10000)

        random_bytes = uuid.uuid4().bytes
        self.db_storage_mock.fetch_historical_data.return_value = io.BytesIO(random_bytes)

        expected_var = random.uniform(-0.5, -0.01)
        expected_cvar = random.uniform(-0.8, -0.05)
        self.monte_carlo_engine_mock.run_simulations.return_value = {
            "var": expected_var,
            "cvar": expected_cvar,
            "simulations": iterations
        }

        result = self.calibrator.calibrate_backtest(portfolio_id, lookback_days, iterations)

        self.assertIn("calibration_id", result)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["iterations"], iterations)
        self.assertEqual(result["metrics"]["var"], expected_var)
        self.assertEqual(result["metrics"]["cvar"], expected_cvar)
        self.db_storage_mock.fetch_historical_data.assert_called_once_with(portfolio_id, lookback_days)
        self.monte_carlo_engine_mock.run_simulations.assert_called_once_with(portfolio_id, lookback_days, iterations)

    def test_calibrate_backtest_insufficient_data(self):
        portfolio_id = uuid.uuid4().hex
        lookback_days = random.randint(1, 10)
        iterations = random.randint(50, 500)

        self.db_storage_mock.fetch_historical_data.return_value = io.BytesIO(b"")

        with self.assertRaises(ValueError) as context:
            self.calibrator.calibrate_backtest(portfolio_id, lookback_days, iterations)

        self.assertIn("Insufficient historical data", str(context.exception))
        self.db_storage_mock.fetch_historical_data.assert_called_once_with(portfolio_id, lookback_days)
        self.monte_carlo_engine_mock.run_simulations.assert_not_called()

    def test_recalibrate_scenario_matrix(self):
        scenario_id = uuid.uuid4().hex
        confidence_level = random.uniform(0.9, 0.99)
        expected_output = {
            "scenario_id": scenario_id,
            "confidence": confidence_level,
            "status": uuid.uuid4().hex
        }

        self.scenario_simulator_mock.evaluate_matrix.return_value = expected_output

        result = self.calibrator.recalibrate_scenario_matrix(scenario_id, confidence_level)

        self.assertEqual(result, expected_output)
        self.scenario_simulator_mock.evaluate_matrix.assert_called_once_with(scenario_id, confidence_level)

    def test_functional_helper_calibrator(self):
        portfolio_id = uuid.uuid4().hex
        target_confidence = random.uniform(0.9, 0.99)
        valuation = {uuid.uuid4().hex: random.random()}
        backtest = {uuid.uuid4().hex: random.random()}
        monte_carlo = {uuid.uuid4().hex: random.random()}

        result = market_portfolio_stress_backtest_calibrator(
            portfolio_id=portfolio_id,
            valuation=valuation,
            backtest=backtest,
            monte_carlo=monte_carlo,
            target_confidence=target_confidence
        )

        self.assertIn("calibration_id", result)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["target_confidence"], target_confidence)
        self.assertEqual(result["valuation"], valuation)
        self.assertEqual(result["backtest"], backtest)
        self.assertEqual(result["monte_carlo"], monte_carlo)
        self.assertEqual(result["status"], "calibrated")

if __name__ == "__main__":
    unittest.main()