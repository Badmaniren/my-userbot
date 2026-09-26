import unittest
import uuid
import random
import os
from skills.market_sentiment_digest import generate_sentiment_portfolio_digest, SentimentPortfolioDigestManager
from skills.market_news_sentiment_analyzer import MarketNewsSentimentAnalyzer
from skills.market_portfolio_digest import PortfolioDigestManager

class TestMarketSentimentDigestIntegration(unittest.TestCase):
    def setUp(self):
        self.random_symbol = f"TEST_{uuid.uuid4().hex[:6].upper()}"
        self.random_url = f"https://example.com/api/market/{uuid.uuid4().hex[:8]}"
        self.random_token = f"bot{random.randint(100000, 999999)}:AAG{uuid.uuid4().hex[:15]}"
        self.random_chat_id = str(random.randint(10000000, 999999999))
        self.storage_file = f"test_storage_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_composition_and_sentiment_integration(self):
        analyzer = MarketNewsSentimentAnalyzer()
        self.assertIsNotNone(analyzer, "MarketNewsSentimentAnalyzer должен успешно инициализироваться в композиции")

        digest_manager = PortfolioDigestManager(self.storage_file)
        self.assertIsNotNone(digest_manager, "PortfolioDigestManager должен успешно инициализироваться в композиции")

        raw_news_snippet = f"Breaking news for {self.random_symbol}: profits soared by {random.randint(10, 90)}% this quarter."
        sentiment_result = analyzer.analyze(raw_news_snippet)
        
        self.assertIsInstance(sentiment_result, dict, "Анализ сентимента должен возвращать словарь")

        digest_output = generate_sentiment_portfolio_digest(
            symbol=self.random_symbol,
            url=self.random_url,
            telegram_token=self.random_token,
            chat_id=self.random_chat_id,
            storage_file=self.storage_file,
            raw_news=raw_news_snippet
        )

        self.assertIsNotNone(digest_output, "Интеграционный дайджест не должен возвращать None")
        
        manager_instance = SentimentPortfolioDigestManager(self.storage_file)
        compiled_data = manager_instance.compile_sentiment_digest(self.random_symbol, self.random_url, raw_news_snippet)
        
        self.assertIsInstance(compiled_data, dict, "Компиляция дайджеста с сентиментом должна возвращать словарь")
        self.assertIn(self.random_symbol, str(compiled_data), "Сгенерированный дайджест должен содержать целевой символ актива")

if __name__ == '__main__':
    unittest.main()