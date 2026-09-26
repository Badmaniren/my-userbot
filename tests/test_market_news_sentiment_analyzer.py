import unittest
from unittest.mock import patch
import io
import uuid
import random
from skills.market_news_sentiment_analyzer import (
    MarketNewsSentimentAnalyzer,
    analyze_news_sentiment,
    parse_market_news
)


class TestMarketNewsSentimentAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = MarketNewsSentimentAnalyzer()
        self.rand_str = uuid.uuid4().hex

    def test_analyze_bullish_sentiment(self):
        kw1 = random.choice(self.analyzer.bullish_keywords)
        kw2 = random.choice(self.analyzer.bullish_keywords)
        text = f"Market showing immense {kw1} and massive {kw2} for investors. [12345678-1234-1234-1234-123456789abc]"
        res = self.analyzer.analyze(text)
        self.assertEqual(res["sentiment"], "bullish")
        self.assertGreater(res["score"], 0.0)
        self.assertIn("identifier", res)

    def test_analyze_bearish_sentiment(self):
        kw1 = random.choice(self.analyzer.bearish_keywords)
        kw2 = random.choice(self.analyzer.bearish_keywords)
        text = f"Sudden {kw1} and critical {kw2} detected in trading volume. ID-12345678-1234-1234-1234-123456789abc"
        res = self.analyzer.analyze(text)
        self.assertEqual(res["sentiment"], "bearish")
        self.assertLess(res["score"], 0.0)
        self.assertEqual(res["identifier"], "12345678-1234-1234-1234-123456789abc")

    def test_analyze_neutral_sentiment(self):
        text = f"Completely neutral market conditions observed today {self.rand_str}."
        res = self.analyzer.analyze(text)
        self.assertEqual(res["sentiment"], "neutral")
        self.assertEqual(res["score"], 0.0)
        self.assertNotIn("identifier", res)

    def test_batch_analyze_stream(self):
        kw_bull = random.choice(self.analyzer.bullish_keywords)
        kw_bear = random.choice(self.analyzer.bearish_keywords)
        file_content = f"Market {kw_bull}\nSevere {kw2 if 'kw2' in locals() else kw_bear}\nNeutral statement {self.rand_str}\n".encode('utf-8')
        
        dynamic_filename = f"temp_{uuid.uuid4().hex}.txt"
        with patch("builtins.open", return_value=io.BytesIO(file_content)) as mock_open:
            with patch("io.BytesIO", return_value=io.BytesIO(file_content)):
                res = self.analyzer.batch_analyze_stream(dynamic_filename)
                self.assertIsInstance(res, list)
                self.assertGreaterEqual(len(res), 2)

    def test_extract_entities(self):
        ticker1 = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=4))
        ticker2 = ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=3))
        text = f"Trading activities for ${ticker1} and ${ticker2} are volatile."
        entities = self.analyzer.extract_entities(text)
        self.assertIn(ticker1, entities)
        self.assertIn(ticker2, entities)

    def test_process_and_store_with_db(self):
        kw = random.choice(self.analyzer.bullish_keywords)
        news_item = f"Token {uuid.uuid4().hex} shows great {kw}"
        with patch("skills.market_news_sentiment_analyzer.db_storage") as mock_db:
            mock_db.save_sentiment_record.return_value = True
            result = self.analyzer.process_and_store(news_item)
            self.assertTrue(result)
            mock_db.save_sentiment_record.assert_called_once()

    def test_process_and_store_without_db(self):
        kw = random.choice(self.analyzer.bearish_keywords)
        news_item = f"Asset experienced severe {kw}"
        with patch("skills.market_news_sentiment_analyzer.db_storage", None):
            result = self.analyzer.process_and_store(news_item)
            self.assertTrue(result)

    def test_analyze_news_sentiment_with_dict(self):
        kw = random.choice(self.analyzer.bullish_keywords)
        uid = str(uuid.uuid4())
        payload = {
            "raw_text": f"Extreme {kw} happening now",
            "identifier": uid
        }
        res = analyze_news_sentiment(payload)
        self.assertEqual(res["sentiment"], "bullish")
        self.assertEqual(res["identifier"], uid)

    def test_analyze_news_sentiment_with_string(self):
        kw = random.choice(self.analyzer.bearish_keywords)
        text = f"Massive market {kw} event"
        res = analyze_news_sentiment(text)
        self.assertEqual(res["sentiment"], "bearish")

    def test_analyze_news_sentiment_fallback(self):
        res = analyze_news_sentiment(12345)
        self.assertEqual(res["sentiment"], "neutral")
        self.assertEqual(res["score"], 0.0)

    def test_parse_market_news(self):
        uid = str(uuid.uuid4())
        snippet = f"ID-{uid}: breaking news about financial markets {self.rand_str}"
        parsed = parse_market_news(snippet)
        self.assertEqual(parsed["identifier"], uid)
        self.assertEqual(parsed["raw_text"], snippet)


if __name__ == '__main__':
    unittest.main()