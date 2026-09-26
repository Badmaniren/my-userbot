import json
import os
import requests
from skills.market_news_sentiment_analyzer import MarketNewsSentimentAnalyzer
from skills.market_portfolio_digest import PortfolioDigestManager


class MarketSentimentDigestEngine:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.analyzer = MarketNewsSentimentAnalyzer()
        self.manager = PortfolioDigestManager(storage_file)

    def compile_sentiment_digest(self, symbol: str, url: str, raw_news: str = None):
        digest = self.manager.compile_digest(symbol, url)
        sentiment = None
        if raw_news:
            sentiment = self.analyzer.analyze(raw_news)
        return {
            "digest": digest,
            "sentiment": sentiment
        }

    def process_sentiment_stream_and_digest(self, filename: str, symbol: str, url: str):
        stream_analysis = self.analyzer.batch_analyze_stream(filename)
        digest = self.manager.compile_digest(symbol, url)
        return {
            "stream_analysis": stream_analysis,
            "digest": digest
        }

    def fetch_raw_feed(self, url: str) -> bytes:
        response = requests.get(url, timeout=10)
        return response.content


class SentimentPortfolioDigestManager(PortfolioDigestManager):
    def __init__(self, storage_file: str):
        super().__init__(storage_file)
        self.analyzer = MarketNewsSentimentAnalyzer()

    def compile_sentiment_digest(self, symbol: str, url: str, raw_news: str = None):
        digest = self.compile_digest(symbol, url)
        sentiment = None
        if raw_news:
            sentiment = self.analyzer.analyze(raw_news)
        return {
            "symbol": symbol,
            "digest": digest,
            "sentiment": sentiment
        }


def generate_sentiment_portfolio_digest(
    symbol: str,
    url: str,
    telegram_token: str,
    chat_id: str,
    storage_file: str,
    raw_news: str = None
):
    analyzer = MarketNewsSentimentAnalyzer()
    manager = PortfolioDigestManager(storage_file)

    if raw_news:
        sentiment = analyzer.analyze(raw_news)
    else:
        sentiment = analyzer.analyze(f"Market update for {symbol}")

    if not os.path.exists(storage_file):
        with open(storage_file, 'w', encoding='utf-8') as f:
            json.dump({symbol: {"status": "initialized", "url": url}}, f)

    digest = manager.compile_digest(symbol, url)
    manager.render_and_send(symbol, telegram_token, chat_id)

    return {
        "sentiment": sentiment,
        "digest": digest
    }