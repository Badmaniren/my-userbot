import unittest
import uuid
import random
from skills.market_sentiment_anomaly_correlator import (
    MarketSentimentAnomalyCorrelator,
    market_sentiment_anomaly_correlator
)

class TestMarketSentimentAnomalyCorrelatorIntegration(unittest.TestCase):
    def setUp(self):
        self.correlator = MarketSentimentAnomalyCorrelator()
        self.test_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.test_news = f"Market volatility surges unexpectedly as random factor {random.randint(1000, 9999)} impacts the sector negatively."

    def test_correlate_real_execution(self):
        result = self.correlator.correlate(self.test_ticker, self.test_news)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("ticker"), self.test_ticker)
        self.assertIn("anomaly", result)
        self.assertIn("sentiment", result)
        self.assertIn("correlation_index", result)
        self.assertIsInstance(result["correlation_index"], float)

    def test_market_sentiment_anomaly_correlator_function_wrapper(self):
        random_anomaly_score = round(random.uniform(0.1, 5.0), 2)
        random_sentiment_score = round(random.uniform(-1.0, 1.0), 2)

        payload = {
            "ticker": self.test_ticker,
            "anomaly": {"anomaly_score": random_anomaly_score},
            "sentiment": {"sentiment": random_sentiment_score}
        }

        output = market_sentiment_anomaly_correlator(payload)

        self.assertIsInstance(output, dict)
        self.assertEqual(output.get("ticker"), self.test_ticker)
        self.assertEqual(output.get("status"), "CORRELATED")
        self.assertIn("correlation_id", output)
        self.assertTrue(len(output["correlation_id"]) > 0)

        expected_index = round(float(random_anomaly_score) * abs(float(random_sentiment_score)), 4)
        self.assertEqual(output.get("correlation_index"), expected_index)

if __name__ == '__main__':
    unittest.main()