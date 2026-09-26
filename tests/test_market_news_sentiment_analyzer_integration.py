import unittest
import uuid
import tempfile
import os
from skills.market_news_sentiment_analyzer import (
    MarketNewsSentimentAnalyzer,
    analyze_news_sentiment,
    parse_market_news
)
from skills import db_storage

class TestMarketNewsSentimentAnalyzerIntegration(unittest.TestCase):
    def test_end_to_end_sentiment_pipeline(self):
        random_id = str(uuid.uuid4())
        random_token = str(uuid.uuid4()).replace("-", "")
        ticker = "TSLA"
        
        raw_news = (
            f"ID-{random_id}: Massive profit and surge in growth for ${ticker}. "
            f"The breakout rally showed bullish momentum token {random_token}."
        )
        
        parsed = parse_market_news(raw_news)
        self.assertEqual(parsed["identifier"], random_id)
        self.assertEqual(parsed["raw_text"], raw_news)
        
        analysis = analyze_news_sentiment(parsed)
        self.assertEqual(analysis["sentiment"], "bullish")
        self.assertGreater(analysis["score"], 0.0)
        self.assertEqual(analysis["identifier"], random_id)
        
        analyzer = MarketNewsSentimentAnalyzer()
        entities = analyzer.extract_entities(raw_news)
        self.assertIn(ticker, entities)
        
        stored_successfully = analyzer.process_and_store(raw_news)
        self.assertTrue(stored_successfully)

    def test_batch_stream_integration(self):
        random_id_1 = str(uuid.uuid4())
        random_id_2 = str(uuid.uuid4())
        
        line1 = f"ID-{random_id_1}: Company reports a massive crash and total loss. Bearish panic."
        line2 = f"ID-{random_id_2}: Steady earnings and extraordinary upward momentum. Bullish gain."
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as tf:
            tf.write(f"{line1}\n{line2}\n")
            temp_filename = tf.name
            
        try:
            analyzer = MarketNewsSentimentAnalyzer()
            results = analyzer.batch_analyze_stream(temp_filename)
            
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["sentiment"], "bearish")
            self.assertEqual(results[0]["identifier"], random_id_1)
            
            self.assertEqual(results[1]["sentiment"], "bullish")
            self.assertEqual(results[1]["identifier"], random_id_2)
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

if __name__ == '__main__':
    unittest.main()