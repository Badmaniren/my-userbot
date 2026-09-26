import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import io

from skills.market_sentiment_telegram_publisher import (
    MarketSentimentTelegramPublisher,
    publish_sentiment_with_urgency,
    publish_market_sentiment_digest,
    URGENCY_LEVELS
)


class TestMarketSentimentTelegramPublisher(unittest.TestCase):

    def setUp(self):
        self.token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"https://example.com/market/{uuid.uuid4().hex}"

    def test_urgency_levels_mapping(self):
        self.assertEqual(URGENCY_LEVELS["LOW"], 1)
        self.assertEqual(URGENCY_LEVELS["MEDIUM"], 2)
        self.assertEqual(URGENCY_LEVELS["HIGH"], 3)
        self.assertEqual(URGENCY_LEVELS["CRITICAL"], 4)

    def test_should_publish_filtering(self):
        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.token,
            chat_id=self.chat_id,
            min_urgency="HIGH"
        )
        self.assertFalse(publisher.should_publish("LOW"))
        self.assertFalse(publisher.should_publish("MEDIUM"))
        self.assertTrue(publisher.should_publish("HIGH"))
        self.assertTrue(publisher.should_publish("CRITICAL"))

    def test_publisher_token_aliases(self):
        alt_token = uuid.uuid4().hex
        pub1 = MarketSentimentTelegramPublisher(token=alt_token)
        self.assertEqual(pub1.telegram_token, alt_token)
        self.assertEqual(pub1.token, alt_token)

        pub2 = MarketSentimentTelegramPublisher(telegram_token=alt_token)
        self.assertEqual(pub2.telegram_token, alt_token)
        self.assertEqual(pub2.token, alt_token)

    @patch("skills.market_sentiment_telegram_publisher.MarketSentimentDigestEngine")
    @patch("skills.market_sentiment_telegram_publisher.send_telegram_notification")
    def test_publish_digest_below_min_urgency(self, mock_send, mock_engine_cls):
        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.token,
            chat_id=self.chat_id,
            min_urgency="HIGH"
        )
        res = publisher.publish_digest(
            symbol=self.symbol,
            url=self.url,
            raw_news=uuid.uuid4().hex,
            urgency="LOW"
        )
        self.assertFalse(res)
        mock_send.assert_not_called()
        mock_engine_cls.assert_not_called()

    @patch("skills.market_sentiment_telegram_publisher.MarketSentimentDigestEngine")
    @patch("skills.market_sentiment_telegram_publisher.send_telegram_notification")
    def test_publish_digest_success(self, mock_send, mock_engine_cls):
        mock_send.return_value = True
        mock_engine_instance = mock_engine_cls.return_value
        expected_digest = uuid.uuid4().hex
        mock_engine_instance.compile_sentiment_digest.return_value = expected_digest

        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            min_urgency="LOW"
        )
        
        raw_news_data = uuid.uuid4().hex
        res = publisher.publish_digest(
            symbol=self.symbol,
            url=self.url,
            raw_news=raw_news_data,
            urgency="MEDIUM"
        )

        self.assertTrue(res)
        mock_engine_cls.assert_called_once_with(self.storage_file)
        mock_engine_instance.compile_sentiment_digest.assert_called_once_with(
            self.symbol, self.url, raw_news_data
        )
        mock_send.assert_called_once()
        called_args = mock_send.call_args[0]
        self.assertEqual(called_args[0], self.token)
        self.assertEqual(called_args[1], self.chat_id)
        self.assertIn(self.symbol, called_args[2])
        self.assertIn(expected_digest, called_args[2])

    @patch("skills.market_sentiment_telegram_publisher.MarketSentimentDigestEngine")
    @patch("skills.market_sentiment_telegram_publisher.send_telegram_notification")
    def test_publish_digest_fetches_raw_feed_if_none(self, mock_send, mock_engine_cls):
        mock_send.return_value = None
        mock_engine_instance = mock_engine_cls.return_value
        fetched_feed = f"feed_{uuid.uuid4().hex}".encode("utf-8")
        mock_engine_instance.fetch_raw_feed.return_value = fetched_feed
        expected_digest = uuid.uuid4().hex
        mock_engine_instance.compile_sentiment_digest.return_value = expected_digest

        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            min_urgency="LOW"
        )

        res = publisher.publish_digest(
            symbol=self.symbol,
            url=self.url,
            raw_news=None,
            urgency="LOW"
        )

        self.assertTrue(res)
        mock_engine_instance.fetch_raw_feed.assert_called_once_with(self.url)
        mock_engine_instance.compile_sentiment_digest.assert_called_once_with(
            self.symbol, self.url, fetched_feed.decode("utf-8")
        )

    @patch("skills.market_sentiment_telegram_publisher.MarketSentimentDigestEngine")
    @patch("skills.market_sentiment_telegram_publisher.send_telegram_notification")
    def test_publish_digest_fetch_feed_exception_handled(self, mock_send, mock_engine_cls):
        mock_send.return_value = True
        mock_engine_instance = mock_engine_cls.return_value
        mock_engine_instance.fetch_raw_feed.side_effect = Exception("Network failure")
        expected_digest = uuid.uuid4().hex
        mock_engine_instance.compile_sentiment_digest.return_value = expected_digest

        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            min_urgency="LOW"
        )

        res = publisher.publish_digest(
            symbol=self.symbol,
            url=self.url,
            raw_news=None,
            urgency="LOW"
        )

        self.assertTrue(res)
        mock_engine_instance.fetch_raw_feed.assert_called_once_with(self.url)
        mock_engine_instance.compile_sentiment_digest.assert_called_once_with(
            self.symbol, self.url, ""
        )

    @patch("skills.market_sentiment_telegram_publisher.send_telegram_notification")
    def test_publish_critical_sentiment(self, mock_send):
        mock_send.return_value = True
        metric = uuid.uuid4().hex
        details = uuid.uuid4().hex

        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.token,
            chat_id=self.chat_id,
            min_urgency="HIGH"
        )

        res = publisher.publish_critical_sentiment(
            symbol=self.symbol,
            sentiment_metric=metric,
            details=details,
            urgency="CRITICAL"
        )

        self.assertTrue(res)
        mock_send.assert_called_once()
        msg = mock_send.call_args[0][2]
        self.assertIn("CRITICAL SENTIMENT ALERT", msg)
        self.assertIn(self.symbol, msg)
        self.assertIn(metric, msg)
        self.assertIn(details, msg)

    @patch("skills.market_sentiment_telegram_publisher.send_telegram_notification")
    def test_publish_critical_sentiment_below_urgency(self, mock_send):
        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.token,
            chat_id=self.chat_id,
            min_urgency="CRITICAL"
        )

        res = publisher.publish_critical_sentiment(
            symbol=self.symbol,
            sentiment_metric=uuid.uuid4().hex,
            details=uuid.uuid4().hex,
            urgency="LOW"
        )

        self.assertFalse(res)
        mock_send.assert_not_called()

    @patch("skills.market_sentiment_telegram_publisher.send_telegram_notification")
    def test_publish_critical_alert(self, mock_send):
        mock_send.return_value = True
        alert_msg = uuid.uuid4().hex

        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.token,
            chat_id=self.chat_id,
            min_urgency="MEDIUM"
        )

        res = publisher.publish_critical_alert(
            symbol=self.symbol,
            message=alert_msg,
            urgency="HIGH"
        )

        self.assertTrue(res)
        mock_send.assert_called_once()
        sent_text = mock_send.call_args[0][2]
        self.assertIn("CRITICAL ALERT", sent_text)
        self.assertIn(self.symbol, sent_text)
        self.assertIn(alert_msg, sent_text)

    @patch("skills.market_sentiment_telegram_publisher.send_telegram_notification")
    def test_publish_critical_alert_below_urgency(self, mock_send):
        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.token,
            chat_id=self.chat_id,
            min_urgency="CRITICAL"
        )

        res = publisher.publish_critical_alert(
            symbol=self.symbol,
            message=uuid.uuid4().hex,
            urgency="MEDIUM"
        )

        self.assertFalse(res)
        mock_send.assert_not_called()

    @patch("skills.market_sentiment_telegram_publisher.MarketSentimentTelegramPublisher.publish_digest")
    def test_publish_sentiment_with_urgency_entrypoint(self, mock_publish_digest):
        mock_publish_digest.return_value = True
        raw_news = uuid.uuid4().hex

        res = publish_sentiment_with_urgency(
            token=self.token,
            chat_id=self.chat_id,
            symbol=self.symbol,
            url=self.url,
            raw_news=raw_news,
            urgency="HIGH",
            min_urgency="MEDIUM",
            storage_file=self.storage_file
        )

        self.assertTrue(res)
        mock_publish_digest.assert_called_once_with(
            symbol=self.symbol,
            url=self.url,
            raw_news=raw_news,
            urgency="HIGH"
        )

    @patch("skills.market_sentiment_telegram_publisher.MarketSentimentTelegramPublisher.publish_digest")
    def test_publish_market_sentiment_digest_entrypoint(self, mock_publish_digest):
        mock_publish_digest.return_value = True
        raw_news = uuid.uuid4().hex

        res = publish_market_sentiment_digest(
            symbol=self.symbol,
            url=self.url,
            raw_news=raw_news,
            token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file,
            urgency="MEDIUM",
            min_urgency="LOW"
        )

        self.assertTrue(res)
        mock_publish_digest.assert_called_once_with(
            symbol=self.symbol,
            url=self.url,
            raw_news=raw_news,
            urgency="MEDIUM"
        )