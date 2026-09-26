import os
import random
import tempfile
import unittest
import uuid
from skills.market_sentiment_telegram_publisher import (
    MarketSentimentTelegramPublisher,
    publish_sentiment_with_urgency,
    publish_market_sentiment_digest,
    URGENCY_LEVELS,
)


class TestMarketSentimentTelegramPublisherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(
            self.test_dir.name, f"sentiment_store_{uuid.uuid4().hex}.json"
        )
        self.token = f"bot{uuid.uuid4().hex}:{uuid.uuid4().hex}"
        self.chat_id = str(random.randint(10000000, 99999999))
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://news.example.com/{uuid.uuid4().hex}"

    def tearDown(self):
        self.test_dir.cleanup()

    def test_urgency_filtering(self):
        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            min_urgency="HIGH",
        )

        self.assertFalse(publisher.should_publish("LOW"))
        self.assertFalse(publisher.should_publish("MEDIUM"))
        self.assertTrue(publisher.should_publish("HIGH"))
        self.assertTrue(publisher.should_publish("CRITICAL"))

        raw_news = f"Quarterly profits surge for {self.symbol} by {random.randint(10, 50)}%."
        filtered_result = publisher.publish_digest(
            symbol=self.symbol,
            url=self.url,
            raw_news=raw_news,
            urgency="LOW",
        )
        self.assertFalse(filtered_result)

    def test_publish_digest_flow_and_engine_integration(self):
        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            min_urgency="LOW",
        )

        random_metric = random.randint(100, 999)
        raw_news = f"Strong positive sentiment detected for {self.symbol} with score {random_metric}."

        result = publisher.publish_digest(
            symbol=self.symbol,
            url=self.url,
            raw_news=raw_news,
            urgency="MEDIUM",
        )
        self.assertIsInstance(result, bool)

    def test_publish_critical_sentiment_and_alert(self):
        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            min_urgency="HIGH",
        )

        unique_metric = f"METRIC_{uuid.uuid4().hex[:8]}"
        unique_details = f"Anomaly drop {random.uniform(5.0, 25.0):.2f}%"

        result_sent = publisher.publish_critical_sentiment(
            symbol=self.symbol,
            sentiment_metric=unique_metric,
            details=unique_details,
            urgency="CRITICAL",
        )
        self.assertIsInstance(result_sent, bool)

        unique_msg = f"Alert trigger {uuid.uuid4().hex}"
        result_alert = publisher.publish_critical_alert(
            symbol=self.symbol,
            message=unique_msg,
            urgency="CRITICAL",
        )
        self.assertIsInstance(result_alert, bool)

        result_suppressed = publisher.publish_critical_alert(
            symbol=self.symbol,
            message=unique_msg,
            urgency="LOW",
        )
        self.assertFalse(result_suppressed)

    def test_publish_sentiment_with_urgency_helper(self):
        raw_news = f"Market volatility indicator for {self.symbol} is high: {uuid.uuid4().hex}"
        res_skipped = publish_sentiment_with_urgency(
            token=self.token,
            chat_id=self.chat_id,
            symbol=self.symbol,
            url=self.url,
            raw_news=raw_news,
            urgency="LOW",
            min_urgency="CRITICAL",
            storage_file=self.storage_file,
        )
        self.assertFalse(res_skipped)

        res_passed = publish_sentiment_with_urgency(
            token=self.token,
            chat_id=self.chat_id,
            symbol=self.symbol,
            url=self.url,
            raw_news=raw_news,
            urgency="CRITICAL",
            min_urgency="HIGH",
            storage_file=self.storage_file,
        )
        self.assertIsInstance(res_passed, bool)

    def test_publish_market_sentiment_digest_helper(self):
        raw_news = f"Digest update {uuid.uuid4().hex} for symbol {self.symbol}"
        res = publish_market_sentiment_digest(
            symbol=self.symbol,
            url=self.url,
            raw_news=raw_news,
            token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            urgency="MEDIUM",
            min_urgency="LOW",
        )
        self.assertIsInstance(res, bool)


if __name__ == "__main__":
    unittest.main()