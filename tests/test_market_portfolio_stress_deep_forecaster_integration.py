import unittest
import uuid
import random

from skills.market_portfolio_stress_deep_forecaster import (
    start_new,
    market_portfolio_stress_deep_forecaster
)


class TestMarketPortfolioStressDeepForecasterIntegration(unittest.TestCase):

    def test_start_new_integration_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        confidence = round(random.uniform(0.80, 0.99), 2)

        result = start_new(portfolio_id=portfolio_id, confidence=confidence)

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertEqual(result.get("confidence"), confidence)
        self.assertIn("historical_data", result)
        self.assertIn("scenario_result", result)
        self.assertIn("ml_stress_prediction", result)
        self.assertIn("audit_id", result)

    def test_deep_forecaster_integration_flow(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        anomaly_insights = {"anomaly_score": round(random.uniform(0.0, 1.0), 4)}
        scenario_evaluations = {"var_95": round(random.uniform(-5000.0, -100.0), 2)}

        result = market_portfolio_stress_deep_forecaster(
            portfolio_id=portfolio_id,
            anomaly_insights=anomaly_insights,
            scenario_evaluations=scenario_evaluations
        )

        self.assertIsInstance(result, dict)
        self.assertIn("forecast_id", result)
        self.assertTrue(result["forecast_id"].startswith("fc_"))
        self.assertEqual(result.get("portfolio_id"), portfolio_id)
        self.assertIsInstance(result.get("stress_probability"), float)
        self.assertEqual(result.get("anomaly_insights"), anomaly_insights)
        self.assertEqual(result.get("scenario_evaluations"), scenario_evaluations)


if __name__ == "__main__":
    unittest.main()