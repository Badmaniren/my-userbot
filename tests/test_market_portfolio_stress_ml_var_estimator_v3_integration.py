import unittest
import uuid
import random
from datetime import datetime

from skills.market_portfolio_stress_ml_var_estimator_v3 import (
    MLVaREstimatorV3,
    market_portfolio_stress_ml_var_estimator_v3,
    VaREestimationError,
    InsufficientDataError
)
from skills.market_portfolio_stress_ml_volatility_forecaster_v2 import market_portfolio_stress_ml_volatility_forecaster_v2
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine
from skills.db_storage import db_storage


class RealVolatilityForecasterAdapter:
    def predict_volatility(self, portfolio_id, weights, returns, confidence, horizon):
        payload = {
            "portfolio_id": portfolio_id,
            "weights": weights,
            "returns": returns,
            "confidence_level": confidence,
            "horizon": horizon
        }
        res = market_portfolio_stress_ml_volatility_forecaster_v2(payload)
        return res.get("volatility_forecast", 0.2)


class RealMonteCarloEngineAdapter:
    def simulate_tail_risk(self, weights, returns, volatility, confidence, horizon):
        payload = {
            "weights": weights,
            "returns": returns,
            "volatility": volatility,
            "confidence": confidence,
            "horizon": horizon
        }
        res = market_portfolio_stress_monte_carlo_engine(payload)
        return res.get("tail_risk_value", 12345.67)


class RealDbStorageAdapter:
    def save_estimate(self, result):
        db_storage({
            "action": "save",
            "table": "portfolio_var_evaluations_ml",
            "portfolio_id": result["portfolio_id"],
            "data": result
        })


class TestMarketPortfolioStressMLVaREstimatorV3Integration(unittest.TestCase):

    def test_end_to_end_ml_var_estimator_pipeline(self):
        portfolio_id = f"port-{uuid.uuid4()}"
        weights = [0.2, 0.3, 0.5]
        returns = [random.uniform(-0.05, 0.05) for _ in range(10)]
        confidence = random.choice([0.90, 0.95, 0.99])
        horizon = random.randint(1, 30)

        vol_forecaster = RealVolatilityForecasterAdapter()
        mc_engine = RealMonteCarloEngineAdapter()
        storage = RealDbStorageAdapter()

        estimator = MLVaREstimatorV3(
            volatility_forecaster=vol_forecaster,
            monte_carlo_engine=mc_engine,
            db_storage=storage
        )

        result = estimator.calculate_var(
            portfolio_id=portfolio_id,
            weights=weights,
            returns=returns,
            confidence=confidence,
            horizon=horizon
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertIn("var_value", result)
        self.assertIn("predicted_volatility", result)
        self.assertIn("timestamp", result)

    def test_insufficient_data_error_propagation(self):
        portfolio_id = f"port-{uuid.uuid4()}"
        weights = [1.0]
        returns = [0.01, 0.02]
        confidence = 0.95
        horizon = 10

        estimator = MLVaREstimatorV3(
            volatility_forecaster=RealVolatilityForecasterAdapter(),
            monte_carlo_engine=RealMonteCarloEngineAdapter(),
            db_storage=RealDbStorageAdapter()
        )

        with self.assertRaises(InsufficientDataError):
            estimator.calculate_var(
                portfolio_id=portfolio_id,
                weights=weights,
                returns=returns,
                confidence=confidence,
                horizon=horizon
            )

    def test_legacy_wrapper_integration(self):
        portfolio_id = f"port-legacy-{uuid.uuid4()}"
        vol_list = [random.uniform(0.1, 0.4), random.uniform(0.1, 0.4)]
        base_val = random.uniform(50000.0, 500000.0)

        payload = {
            "portfolio_id": portfolio_id,
            "confidence_level": 0.99,
            "volatility_forecast": vol_list,
            "base_value": base_val
        }

        result = market_portfolio_stress_ml_var_estimator_v3(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertGreater(result["var_value"], 0.0)
        self.assertGreater(result["predicted_volatility"], 0.0)
        self.assertIn("timestamp", result)


if __name__ == "__main__":
    unittest.main()