import unittest
import os
import uuid
import random
from skills.market_portfolio_sentiment_stress_correlator import MarketPortfolioSentimentStressCorrelator, correlate_sentiment_with_stress

class TestMarketPortfolioSentimentStressCorrelatorIntegration(unittest.TestCase):
    def setUp(self):
        self.correlator = MarketPortfolioSentimentStressCorrelator()
        self.portfolio_id = f"portfolio-{uuid.uuid4()}"
        self.news_text = f"Market is experiencing extreme volatility and panic due to unexpected news {uuid.uuid4()}."
        self.window = random.randint(10, 90)

    def test_correlate_real_integration(self):
        result = self.correlator.correlate(
            portfolio_id=self.portfolio_id,
            news_text=self.news_text,
            window=self.window
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("portfolio_id"), self.portfolio_id)
        self.assertIn("correlation_coefficient", result)
        self.assertIn("panic_sensitivity_index", result)
        self.assertIn("sentiment_data", result)
        self.assertIn("stress_data", result)

        sentiment_score = result["sentiment_data"].get("sentiment_score", 0.0)
        self.assertIsInstance(sentiment_score, float)

    def test_correlate_sentiment_with_stress_file_creation(self):
        correlation_factor = round(random.uniform(0.5, 2.0), 2)
        payload = {
            "portfolio_id": self.portfolio_id,
            "sentiment_data": {"sentiment_score": round(random.uniform(-1.0, 1.0), 2)},
            "stress_matrix": {"max_drawdown": round(random.uniform(5.0, 50.0), 2)},
            "correlation_factor": correlation_factor
        }

        output_path = f"reports/sentiment_stress_{self.portfolio_id}.json"
        if os.path.exists(output_path):
            os.remove(output_path)

        res = correlate_sentiment_with_stress(payload)

        self.assertEqual(res.get("portfolio_id"), self.portfolio_id)
        self.assertIn("sensitivity_index", res)
        self.assertTrue(os.path.exists(output_path), "Файл отчета не был создан на диске")

        if os.path.exists(output_path):
            os.remove(output_path)

if __name__ == "__main__":
    unittest.main()