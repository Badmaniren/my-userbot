import unittest
import uuid
import random
from skills.market_sentiment_anomaly_correlator import MarketSentimentAnomalyCorrelator
from skills.market_news_sentiment_analyzer import MarketNewsSentimentAnalyzer
from skills.market_anomaly_detector import MarketAnomalyDetector

class TestMarketSentimentAnomalyCorrelatorIntegration(unittest.TestCase):
    def setUp(self):
        self.correlator = MarketSentimentAnomalyCorrelator()
        self.random_ticker = f"TICK_{uuid.uuid4().hex[:6].upper()}"
        self.random_sentiment = round(random.uniform(-1.0, 1.0), 2)
        self.random_news_text = f"Market crash anticipated for {self.random_ticker} due to unexpected regulatory changes and supply chain disruptions."

    def test_correlate_integration_real_skills(self):
        news_input = {
            "ticker": self.random_ticker,
            "text": self.random_news_text,
            "score": self.random_sentiment
        }

        result = self.correlator.correlate(news_input)

        self.assertIsInstance(result, dict, "Result should be a dictionary")
        self.assertIn("correlation_id", result, "Result must contain correlation_id")
        self.assertIn("ticker", result, "Result must contain ticker")
        self.assertEqual(result["ticker"], self.random_ticker, "Ticker should match input")
        self.assertIn("correlation_found", result, "Result must contain correlation_found flag")
        self.assertIn("sentiment_score", result, "Result must contain sentiment_score")
        self.assertIn("anomaly_data", result, "Result must contain anomaly_data dictionary")
        self.assertIsInstance(result["anomaly_data"], dict, "anomaly_data must be a dictionary")

    def test_process_stream_correlation_integration(self):
        random_filename = f"stream_data_{uuid.uuid4().hex}.txt"
        stream_anomaly_info = {"status": "monitoring", "exchange": "NASDAQ", "id": str(uuid.uuid4())}

        result = self.correlator.process_stream_correlation(random_filename, stream_anomaly=stream_anomaly_info)

        self.assertIsInstance(result, dict, "Stream correlation result should be a dictionary")
        self.assertEqual(result.get("status"), "success", "Status should be success")
        self.assertIn("processed_items_count", result, "Should contain processed items count")
        self.assertEqual(result.get("stream_anomaly_info"), stream_anomaly_info, "Stream anomaly info should match")

if __name__ == "__main__":
    unittest.main()