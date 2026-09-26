import os
from skills.market_sentiment_digest import MarketSentimentDigestEngine
from skills.market_portfolio_telegram_notifier import send_telegram_notification

URGENCY_LEVELS = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}


class MarketSentimentTelegramPublisher:
    def __init__(
        self,
        telegram_token=None,
        chat_id=None,
        storage_file=None,
        min_urgency="LOW",
        token=None,
    ):
        self.telegram_token = telegram_token if telegram_token is not None else token
        self.token = self.telegram_token
        self.chat_id = chat_id
        self.storage_file = storage_file
        self.min_urgency = str(min_urgency).upper()

    def should_publish(self, urgency):
        u_val = URGENCY_LEVELS.get(str(urgency).upper(), 1)
        min_val = URGENCY_LEVELS.get(self.min_urgency, 1)
        return u_val >= min_val

    def publish_digest(self, symbol, url, raw_news=None, urgency="LOW"):
        if not self.should_publish(urgency):
            return False

        engine = MarketSentimentDigestEngine(self.storage_file)
        if raw_news is None and hasattr(engine, "fetch_raw_feed"):
            try:
                raw_news = engine.fetch_raw_feed(url)
                if isinstance(raw_news, bytes):
                    raw_news = raw_news.decode("utf-8", errors="ignore")
            except Exception:
                raw_news = ""

        digest_payload = engine.compile_sentiment_digest(symbol, url, raw_news)
        msg = f"Symbol: {symbol}\nURL: {url}\nUrgency: {urgency}\n{digest_payload}"
        success = send_telegram_notification(self.telegram_token, self.chat_id, msg)
        if success is None:
            return True
        return bool(success)

    def publish_critical_sentiment(
        self, symbol, sentiment_metric, details, urgency="CRITICAL"
    ):
        if not self.should_publish(urgency):
            return False

        msg = (
            f"CRITICAL SENTIMENT ALERT\n"
            f"Symbol: {symbol}\n"
            f"Metric: {sentiment_metric}\n"
            f"Details: {details}\n"
            f"Urgency: {urgency}"
        )
        success = send_telegram_notification(self.telegram_token, self.chat_id, msg)
        if success is None:
            return True
        return bool(success)

    def publish_critical_alert(self, symbol, message, urgency="CRITICAL"):
        if not self.should_publish(urgency):
            return False

        msg = f"CRITICAL ALERT\nSymbol: {symbol}\nMessage: {message}\nUrgency: {urgency}"
        success = send_telegram_notification(self.telegram_token, self.chat_id, msg)
        if success is None:
            return True
        return bool(success)


def publish_sentiment_with_urgency(
    token,
    chat_id,
    symbol,
    url,
    raw_news=None,
    urgency="LOW",
    min_urgency="LOW",
    storage_file=None,
):
    publisher = MarketSentimentTelegramPublisher(
        telegram_token=token,
        chat_id=chat_id,
        storage_file=storage_file,
        min_urgency=min_urgency,
    )
    return publisher.publish_digest(
        symbol=symbol, url=url, raw_news=raw_news, urgency=urgency
    )


def publish_market_sentiment_digest(
    symbol,
    url,
    raw_news,
    token,
    chat_id,
    storage_file=None,
    urgency="LOW",
    min_urgency="LOW",
):
    publisher = MarketSentimentTelegramPublisher(
        telegram_token=token,
        chat_id=chat_id,
        storage_file=storage_file,
        min_urgency=min_urgency,
    )
    return publisher.publish_digest(
        symbol=symbol, url=url, raw_news=raw_news, urgency=urgency
    )