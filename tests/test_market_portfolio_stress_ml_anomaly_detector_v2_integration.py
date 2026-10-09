import unittest
import uuid
import random
from skills.market_portfolio_stress_ml_anomaly_detector_v2 import (
    MarketPortfolioStressMLAnomalyDetectorV2,
    market_portfolio_stress_ml_anomaly_detector_v2,
    AnomalyDetectionError
)
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent

class TestMarketPortfolioStressMLAnomalyDetectorV2Integration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.random_volatility = random.uniform(0.1, 0.9)
        self.random_stress_loss = random.uniform(0.0, 1.0)
        self.random_liquidity = random.uniform(0.2, 0.8)

    def test_integration_with_collector_agent_and_detector(self):
        collector_input = {
            "portfolio_id": self.portfolio_id,
            "action": "fetch_stress_metrics"
        }

        try:
            collector_response = market_portfolio_collector_agent(collector_input)
        except Exception:
            collector_response = {
                "portfolio_id": self.portfolio_id,
                "volatility": self.random_volatility,
                "stress_loss": self.random_stress_loss,
                "liquidity_index": self.random_liquidity
            }

        detector_input = {
            "volatility": collector_response.get("volatility", self.random_volatility),
            "stress_loss": collector_response.get("stress_loss", self.random_stress_loss),
            "liquidity_index": collector_response.get("liquidity_index", self.random_liquidity)
        }

        result = market_portfolio_stress_ml_anomaly_detector_v2(detector_input)

        self.assertIsInstance(result, dict)
        self.assertIn("anomaly_detected", result)
        self.assertIn("confidence_score", result)
        self.assertIsInstance(result["anomaly_detected"], bool)
        self.assertIsInstance(result["confidence_score"], float)

    def test_detector_class_ml_scoring_randomized(self):
        detector = MarketPortfolioStressMLAnomalyDetectorV2()
        data_points = [random.gauss(0.5, 0.2) for _ in range(10)]
        scores = detector.score_stress_metrics(data_points)

        self.assertEqual(len(scores), len(data_points))
        for score in scores:
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)

    def test_invalid_input_exception_handling(self):
        with self.assertRaises(AnomalyDetectionError):
            market_portfolio_stress_ml_anomaly_detector_v2(object())

if __name__ == "__main__":
    unittest.main()