import unittest
import uuid
import random
import os
from skills.market_news_sentiment_analyzer import analyze_news_sentiment
from skills.market_parser import parse_market_news
from skills.db_storage import save_sentiment_record

class TestMarketNewsSentimentAnalyzerIntegration(unittest.TestCase):
    def test_sentiment_analyzer_integration_real_flow(self):
        unique_id = str(uuid.uuid4())
        random_price_factor = round(random.uniform(10.5, 999.9), 2)
        
        raw_news_snippet = (
            f"ID-{unique_id}: Company XYZ reported extraordinary quarterly earnings growth "
            f"with revenue surging by {random_price_factor}%. Market sentiment is overwhelmingly bullish."
        )
        
        parsed_data = parse_market_news(raw_news_snippet)
        self.assertIsNotNone(parsed_data)
        
        sentiment_result = analyze_news_sentiment(parsed_data)
        
        self.assertIsInstance(sentiment_result, dict)
        self.assertIn("sentiment", sentiment_result)
        self.assertIn("score", sentiment_result)
        self.assertEqual(sentiment_result.get("identifier"), unique_id)
        
        storage_status = save_sentiment_record(sentiment_result)
        self.assertTrue(storage_status)

if __name__ == "__main__":
    unittest.main()