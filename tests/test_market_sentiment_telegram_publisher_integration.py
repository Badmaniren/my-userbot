import os
import tempfile
import unittest
import uuid
from skills.market_sentiment_telegram_publisher import (
    MarketSentimentTelegramPublisher,
    publish_market_sentiment_digest,
)


class TestMarketSentimentTelegramPublisherIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.temp_dir.name, f"digest_store_{uuid.uuid4().hex}.json")
        self.token = f"bot_token_{uuid.uuid4().hex[:12]}"
        self.chat_id = f"chat_{uuid.uuid4().hex[:8]}"
        self.symbol = f"SYM_{uuid.uuid4().hex[:5].upper()}"
        self.url = f"https://finance-news.test/{uuid.uuid4().hex}"
        self.unique_marker = f"SURGE_{uuid.uuid4().hex}"
        self.raw_news = (
            f"Breaking: Company {self.symbol} shows remarkable quarter performance. "
            f"Details: {self.unique_marker} observed across all trading desks."
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_filter_blocks_lower_urgency_sentiment(self):
        publisher = MarketSentimentTelegramPublisher(
            token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            min_urgency="HIGH",
        )
        published = publisher.publish_digest(
            symbol=self.symbol,
            url=self.url,
            raw_news=self.raw_news,
            urgency="LOW",
        )
        self.assertFalse(published, "Digest with LOW urgency must be filtered out when min_urgency is HIGH")

    def test_publish_sentiment_digest_above_urgency_creates_storage_and_notifies(self):
        publisher = MarketSentimentTelegramPublisher(
            token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            min_urgency="MEDIUM",
        )
        published = publisher.publish_digest(
            symbol=self.symbol,
            url=self.url,
            raw_news=self.raw_news,
            urgency="HIGH",
        )
        self.assertTrue(published, "Digest with HIGH urgency should be processed and published successfully")
        self.assertTrue(os.path.exists(self.storage_file), "Digest engine must write persistent state to storage_file")
        self.assertGreater(os.path.getsize(self.storage_file), 0, "Storage file must not be empty after compiling digest")

    def test_publish_critical_portfolio_sentiment_alert(self):
        publisher = MarketSentimentTelegramPublisher(
            token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            min_urgency="CRITICAL",
        )
        alert_text = f"CRITICAL SHIFT: Extreme negative sentiment detected for {self.symbol} id {uuid.uuid4().hex}"
        published = publisher.publish_critical_alert(
            symbol=self.symbol,
            message=alert_text,
            urgency="CRITICAL",
        )
        self.assertTrue(published, "Critical sentiment alert must be dispatched through notifier")

    def test_functional_pipeline_entrypoint_with_dynamic_data(self):
        result = publish_market_sentiment_digest(
            symbol=self.symbol,
            url=self.url,
            raw_news=self.raw_news,
            token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            urgency="HIGH",
            min_urgency="LOW",
        )
        self.assertTrue(result, "Direct pipeline invocation should succeed and return True")
        self.assertTrue(os.path.exists(self.storage_file))
        with open(self.storage_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(self.symbol, content, "Generated sentiment digest record must contain target symbol")


if __name__ == "__main__":
    unittest.main()