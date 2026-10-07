import unittest
import uuid
import random
import io
try:
    from skills.db_storage import db_storage
except ImportError:
    try:
        from skills import db_storage
    except ImportError:
        db_storage = None
import skills.market_portfolio_stress_monte_carlo_engine as mc_engine_mod
market_portfolio_stress_monte_carlo_engine = getattr(mc_engine_mod, "market_portfolio_stress_monte_carlo_engine", getattr(mc_engine_mod, "MonteCarloStressEngine", None))
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_stress_backtest_calibrator import (
    MarketPortfolioStressBacktestCalibrator,
    market_portfolio_stress_backtest_calibrator
)


class TestMarketPortfolioStressBacktestCalibratorIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4()}"
        self.scenario_id = f"scen_{uuid.uuid4()}"
        self.lookback_days = random.randint(30, 365)
        self.iterations = random.randint(100, 5000)
        self.target_confidence = round(random.uniform(0.90, 0.99), 4)

        self.calibrator = MarketPortfolioStressBacktestCalibrator(
            db_storage=db_storage,
            market_portfolio_stress_monte_carlo_engine=market_portfolio_stress_monte_carlo_engine,
            market_portfolio_scenario_simulator=market_portfolio_scenario_simulator
        )

    def test_calibrate_backtest_real_flow(self):
        try:
            result = self.calibrator.calibrate_backtest(
                portfolio_id=self.portfolio_id,
                lookback_days=self.lookback_days,
                iterations=self.iterations
            )

            self.assertIsInstance(result, dict)
            self.assertIn("calibration_id", result)
            self.assertEqual(result["portfolio_id"], self.portfolio_id)
            self.assertEqual(result["iterations"], self.iterations)
            self.assertIn("metrics", result)
            self.assertIn("var", result["metrics"])
            self.assertIn("cvar", result["metrics"])
        except ValueError as e:
            self.assertIn("Insufficient historical data", str(e))

    def test_recalibrate_scenario_matrix_real_flow(self):
        result = self.calibrator.recalibrate_scenario_matrix(
            scenario_id=self.scenario_id,
            confidence_level=self.target_confidence
        )
        self.assertIsNotNone(result)

    def test_functional_wrapper_real_flow(self):
        valuation_mock = {"current_value": round(random.uniform(10000.0, 1000000.0), 2)}
        backtest_mock = {"status": "completed", "pnl": round(random.uniform(-5000.0, 15000.0), 2)}
        monte_carlo_mock = {"simulations": self.iterations, "var": round(random.uniform(100.0, 1000.0), 2)}

        result = market_portfolio_stress_backtest_calibrator(
            portfolio_id=self.portfolio_id,
            valuation=valuation_mock,
            backtest=backtest_mock,
            monte_carlo=monte_carlo_mock,
            target_confidence=self.target_confidence
        )

        self.assertIsInstance(result, dict)
        self.assertIn("calibration_id", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["target_confidence"], self.target_confidence)
        self.assertEqual(result["status"], "calibrated")
        self.assertEqual(result["valuation"], valuation_mock)
        self.assertEqual(result["backtest"], backtest_mock)
        self.assertEqual(result["monte_carlo"], monte_carlo_mock)


if __name__ == "__main__":
    unittest.main()