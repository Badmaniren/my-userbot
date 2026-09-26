import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import re

from skills.market_news_sentiment_analyzer import MarketNewsSentimentAnalyzer


class TestMarketNewsSentimentAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = MarketNewsSentimentAnalyzer()

    def test_analyze_sentiment_positive_random(self):
        random_id = uuid.uuid4().hex
        random_word = "".join(random.choices(string.ascii_lowercase, k=8))
        raw_news = f"[{random_id}] Company {random_word} announced record breaking profit, surge, and growth today!"
        
        result = self.analyzer.analyze(raw_news)
        
        self.assertIsInstance(result, dict)
        self.assertIn("sentiment", result)
        self.assertIn("score", result)
        self.assertEqual(result["sentiment"], "bullish")
        self.assertGreater(result["score"], 0)

    def test_analyze_sentiment_negative_random(self):
        random_id = uuid.uuid4().hex
        random_word = "".join(random.choices(string.ascii_lowercase, k=9))
        raw_news = f"[{random_id}] Asset {random_word} suffered a massive drop, crash, and heavy loss in Q3."
        
        result = self.analyzer.analyze(raw_news)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["sentiment"], "bearish")
        self.assertLess(result["score"], 0)

    def test_analyze_sentiment_neutral_random(self):
        random_id = uuid.uuid4().hex
        random_word = "".join(random.choices(string.ascii_lowercase, k=7))
        raw_news = f"[{random_id}] Entity {random_word} held a routine board meeting regarding operational logistics."
        
        result = self.analyzer.analyze(raw_news)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["sentiment"], "neutral")
        self.assertEqual(result["score"], 0.0)

    def test_batch_analyze_with_stream_mock(self):
        random_prefix = uuid.uuid4().hex
        line1 = f"{random_prefix}: Stock surges by {random.randint(10, 99)} percent, massive gain."
        line2 = f"{random_prefix}: Market crash liquidation panic drop."
        
        mock_data = f"{line1}\n{line2}\n".encode('utf-8')
        mock_stream = io.BytesIO(mock_data)

        with patch('skills.market_news_sentiment_analyzer.open', return_value=mock_stream, create=True):
            random_filename = f"{uuid.uuid4().hex}.log"
            results = self.analyzer.batch_analyze_stream(random_filename)
            
            self.assertIsInstance(results, list)
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["sentiment"], "bullish")
            self.assertEqual(results[1]["sentiment"], "bearish")

    def test_extract_keywords_regex_compliance(self):
        random_ticker = "".join(random.choices(string.ascii_uppercase, k=4))
        random_val = random.randint(100, 9999)
        text = f"The stock ${random_ticker} reached an unbelievable target of {random_val} dollars, showing incredible rally momentum."
        
        keywords = self.analyzer.extract_entities(text)
        
        self.assertIsInstance(keywords, list)
        self.assertIn(random_ticker, keywords)

    def test_integration_with_db_storage_mock(self):
        random_hash = uuid.uuid4().hex
        news_item = f"Breaking news for token {random_hash}: explosive breakout and upward trend."
        
        mock_db = MagicMock()
        mock_db.save_sentiment_record.return_value = True

        with patch('skills.market_news_sentiment_analyzer.db_storage', mock_db, create=True):
            res = self.analyzer.process_and_store(news_item)
            self.assertTrue(res)
            mock_db.save_sentiment_record.assert_called_once()
            called_args = mock_db.save_sentiment_record.call_args[0][0]
            self.assertIn(random_hash, str(called_args))


if __name__ == '__main__':
    unittest.main()