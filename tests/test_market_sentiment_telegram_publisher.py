import io
import random
import string
import sys
import unittest
import uuid
from unittest.mock import MagicMock, patch

from skills.market_sentiment_telegram_publisher import (
    MarketSentimentTelegramPublisher,
    publish_sentiment_with_urgency,
)


def _rnd_str(prefix="str"):
    return f"{prefix}_{uuid.uuid4().hex}"


def _rnd_url():
    domain = "".join(random.choices(string.ascii_lowercase, k=8))
    path = "".join(random.choices(string.ascii_lowercase, k=6))
    return f"https://{domain}.org/feed/{path}"


def _rnd_symbol():
    return "".join(random.choices(string.ascii_uppercase, k=4))


class TestMarketSentimentTelegramPublisher(unittest.TestCase):

    def setUp(self):
        self.random_token = _rnd_str("bot_token")
        self.random_chat_id = f"-100{random.randint(100000000, 999999999)}"
        self.random_storage = f"/tmp/{_rnd_str('storage')}.json"
        self.levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]

    def test_publisher_initialization(self):
        min_urgency = random.choice(self.levels)
        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage,
            min_urgency=min_urgency,
        )
        self.assertEqual(publisher.telegram_token, self.random_token)
        self.assertEqual(publisher.chat_id, self.random_chat_id)
        self.assertEqual(publisher.storage_file, self.random_storage)
        self.assertEqual(str(publisher.min_urgency).upper(), min_urgency.upper())

    def test_urgency_filter_logic(self):
        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            min_urgency="HIGH",
        )
        self.assertFalse(publisher.should_publish("LOW"))
        self.assertFalse(publisher.should_publish("MEDIUM"))
        self.assertFalse(publisher.should_publish("low"))
        self.assertTrue(publisher.should_publish("HIGH"))
        self.assertTrue(publisher.should_publish("CRITICAL"))
        self.assertTrue(publisher.should_publish("critical"))

    def test_publish_digest_filtered_out_due_to_low_urgency(self):
        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage,
            min_urgency="CRITICAL",
        )
        test_symbol = _rnd_symbol()
        test_url = _rnd_url()
        test_news = _rnd_str("raw_news")

        with patch(
            "skills.market_sentiment_telegram_publisher.send_telegram_notification"
        ) as mock_notifier, patch(
            "skills.market_sentiment_telegram_publisher.MarketSentimentDigestEngine"
        ) as mock_engine_cls:
            result = publisher.publish_digest(
                symbol=test_symbol,
                url=test_url,
                raw_news=test_news,
                urgency="LOW",
            )
            self.assertFalse(result)
            mock_notifier.assert_not_called()
            mock_engine_cls.assert_not_called()

    def test_publish_digest_success_when_urgency_met(self):
        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage,
            min_urgency="MEDIUM",
        )
        test_symbol = _rnd_symbol()
        test_url = _rnd_url()
        test_news = _rnd_str("raw_news")
        unique_digest_payload = f"DIGEST_PAYLOAD_{uuid.uuid4().hex}"

        with patch(
            "skills.market_sentiment_telegram_publisher.MarketSentimentDigestEngine"
        ) as mock_engine_cls, patch(
            "skills.market_sentiment_telegram_publisher.send_telegram_notification"
        ) as mock_notifier:
            mock_engine_instance = MagicMock()
            mock_engine_cls.return_value = mock_engine_instance
            mock_engine_instance.compile_sentiment_digest.return_value = (
                unique_digest_payload
            )
            mock_notifier.return_value = True

            result = publisher.publish_digest(
                symbol=test_symbol,
                url=test_url,
                raw_news=test_news,
                urgency="HIGH",
            )

            self.assertTrue(result)
            mock_engine_cls.assert_called_once_with(self.random_storage)
            mock_engine_instance.compile_sentiment_digest.assert_called_once_with(
                test_symbol, test_url, test_news
            )
            mock_notifier.assert_called_once()
            called_token, called_chat_id, called_msg = mock_notifier.call_args[0]
            self.assertEqual(called_token, self.random_token)
            self.assertEqual(called_chat_id, self.random_chat_id)
            self.assertIn(unique_digest_payload, called_msg)
            self.assertIn(test_symbol, called_msg)

    def test_publish_digest_handles_notifier_failure(self):
        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage,
            min_urgency="LOW",
        )
        test_symbol = _rnd_symbol()
        test_url = _rnd_url()
        digest_text = _rnd_str("digest")

        with patch(
            "skills.market_sentiment_telegram_publisher.MarketSentimentDigestEngine"
        ) as mock_engine_cls, patch(
            "skills.market_sentiment_telegram_publisher.send_telegram_notification"
        ) as mock_notifier:
            mock_engine_instance = MagicMock()
            mock_engine_cls.return_value = mock_engine_instance
            mock_engine_instance.compile_sentiment_digest.return_value = digest_text
            mock_notifier.return_value = False

            result = publisher.publish_digest(
                symbol=test_symbol,
                url=test_url,
                urgency="LOW",
            )
            self.assertFalse(result)
            mock_notifier.assert_called_once()

    def test_publish_critical_sentiment_alert_success(self):
        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            min_urgency="MEDIUM",
        )
        test_symbol = _rnd_symbol()
        test_score = round(random.uniform(-1.0, 1.0), 4)
        unique_details = _rnd_str("critical_details")

        with patch(
            "skills.market_sentiment_telegram_publisher.send_telegram_notification"
        ) as mock_notifier:
            mock_notifier.return_value = True

            result = publisher.publish_critical_sentiment(
                symbol=test_symbol,
                sentiment_metric=test_score,
                details=unique_details,
                urgency="CRITICAL",
            )

            self.assertTrue(result)
            mock_notifier.assert_called_once()
            called_token, called_chat_id, called_msg = mock_notifier.call_args[0]
            self.assertEqual(called_token, self.random_token)
            self.assertEqual(called_chat_id, self.random_chat_id)
            self.assertIn(test_symbol, called_msg)
            self.assertIn(str(test_score), called_msg)
            self.assertIn(unique_details, called_msg)
            self.assertIn("CRITICAL", called_msg.upper())

    def test_publish_critical_sentiment_alert_filtered_out(self):
        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            min_urgency="CRITICAL",
        )
        test_symbol = _rnd_symbol()
        test_score = round(random.uniform(-1.0, 1.0), 4)
        unique_details = _rnd_str("low_urgency_alert")

        with patch(
            "skills.market_sentiment_telegram_publisher.send_telegram_notification"
        ) as mock_notifier:
            result = publisher.publish_critical_sentiment(
                symbol=test_symbol,
                sentiment_metric=test_score,
                details=unique_details,
                urgency="MEDIUM",
            )
            self.assertFalse(result)
            mock_notifier.assert_not_called()

    def test_publish_sentiment_with_urgency_function(self):
        token = _rnd_str("func_token")
        chat_id = f"-100{random.randint(100000, 999999)}"
        symbol = _rnd_symbol()
        url = _rnd_url()
        raw_news = _rnd_str("func_raw_news")
        storage_file = f"/tmp/{_rnd_str('func_storage')}.db"
        unique_digest = _rnd_str("compiled_digest_res")

        with patch(
            "skills.market_sentiment_telegram_publisher.MarketSentimentDigestEngine"
        ) as mock_engine_cls, patch(
            "skills.market_sentiment_telegram_publisher.send_telegram_notification"
        ) as mock_notifier:
            mock_engine = MagicMock()
            mock_engine_cls.return_value = mock_engine
            mock_engine.compile_sentiment_digest.return_value = unique_digest
            mock_notifier.return_value = True

            res = publish_sentiment_with_urgency(
                token=token,
                chat_id=chat_id,
                symbol=symbol,
                url=url,
                raw_news=raw_news,
                urgency="HIGH",
                min_urgency="MEDIUM",
                storage_file=storage_file,
            )
            self.assertTrue(res)
            mock_engine_cls.assert_called_once_with(storage_file)
            mock_engine.compile_sentiment_digest.assert_called_once_with(
                symbol, url, raw_news
            )
            mock_notifier.assert_called_once()
            _, _, sent_text = mock_notifier.call_args[0]
            self.assertIn(unique_digest, sent_text)

    def test_feed_stream_processing_mock_bytes(self):
        random_payload_bytes = uuid.uuid4().hex.encode("utf-8")
        stream_buffer = io.BytesIO(random_payload_bytes)

        publisher = MarketSentimentTelegramPublisher(
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.random_storage,
            min_urgency="LOW",
        )
        test_symbol = _rnd_symbol()
        test_url = _rnd_url()

        with patch(
            "skills.market_sentiment_telegram_publisher.MarketSentimentDigestEngine"
        ) as mock_engine_cls, patch(
            "skills.market_sentiment_telegram_publisher.send_telegram_notification"
        ) as mock_notifier:
            mock_engine = MagicMock()
            mock_engine_cls.return_value = mock_engine
            mock_engine.fetch_raw_feed.return_value = stream_buffer.read()
            mock_engine.compile_sentiment_digest.return_value = (
                f"Digest from {random_payload_bytes.decode()}"
            )
            mock_notifier.return_value = True

            result = publisher.publish_digest(
                symbol=test_symbol,
                url=test_url,
                raw_news=None,
                urgency="HIGH",
            )
            self.assertTrue(result)
            mock_engine.compile_sentiment_digest.assert_called_once()
            mock_notifier.assert_called_once()

    def test_composition_dependencies_imported(self):
        import skills.market_sentiment_telegram_publisher as mod

        self.assertTrue(
            hasattr(mod, "MarketSentimentDigestEngine")
            or "market_sentiment_digest" in sys.modules,
            "market_sentiment_digest must be imported or used",
        )
        self.assertTrue(
            hasattr(mod, "send_telegram_notification")
            or hasattr(mod, "start_new")
            or "market_portfolio_telegram_notifier" in sys.modules,
            "market_portfolio_telegram_notifier must be imported or used",
        )


if __name__ == "__main__":
    unittest.main()