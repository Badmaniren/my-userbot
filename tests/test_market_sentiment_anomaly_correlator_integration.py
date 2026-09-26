import unittest
import uuid
import random
import os
from skills.market_anomaly_detector import MarketAnomalyDetector
from skills.market_news_sentiment_analyzer import MarketNewsSentimentAnalyzer
from skills.market_sentiment_anomaly_correlator import market_sentiment_anomaly_correlator

class TestMarketSentimentAnomalyCorrelatorIntegration(unittest.TestCase):
    def setUp(self):
        self.ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.random_sentiment_score = round(random.uniform(-1.0, 1.0), 4)
        self.news_text = f"Emergency market update for {self.ticker}: unexpected volume surge with sentiment index {self.random_sentiment_score}"
        
    def test_correlator_integration_pipeline(self):
        anomaly_detector = MarketAnomalyDetector()
        news_analyzer = MarketNewsSentimentAnalyzer()
        
        anomaly_result = anomaly_detector.detect(self.ticker)
        
        news_item = {
            "id": str(uuid.uuid4()),
            "ticker": self.ticker,
            "text": self.news_text,
            "score": self.random_sentiment_score
        }
        sentiment_result = news_analyzer.analyze(news_item)
        
        correlation_input = {
            "ticker": self.ticker,
            "anomaly": anomaly_result,
            "sentiment": sentiment_result
        }
        
        correlator_output = market_sentiment_anomaly_correlator(correlation_input)
        
        self.assertIsInstance(correlator_output, dict, "Correlator must return a dictionary result")
        self.assertIn("correlation_id", correlator_output, "Output must contain a correlation_id")
        self.assertEqual(correlator_output.get("ticker"), self.ticker, "Ticker in output must match input")
        self.assertIn("status", correlator_output, "Output must define a correlation status")

if __name__ == "__main__":
    unittest.main()