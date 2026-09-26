import io
import random
import string
import unittest
from unittest.mock import MagicMock, patch
import requests

from skills.market_news_fetcher import MarketNewsFetcher, extract_tickers


class TestMarketNewsFetcher(unittest.TestCase):

    def setUp(self):
        self.fetcher = MarketNewsFetcher()

    def _random_ticker(self):
        length = random.randint(3, 5)
        return "".join(random.choices(string.ascii_uppercase, k=length))

    def _random_word(self):
        return "".join(random.choices(string.ascii_lowercase, k=random.randint(4, 9)))

    def _random_url(self):
        domain = uuid_str = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        path = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
        return f"https://{domain}.org/news/{path}"

    def test_extract_tickers_cashtag_and_plain(self):
        ticker_1 = self._random_ticker()
        ticker_2 = self._random_ticker()
        ticker_3 = self._random_ticker()

        prefix_words = " ".join([self._random_word() for _ in range(random.randint(2, 5))])
        mid_words = " ".join([self._random_word() for _ in range(random.randint(2, 5))])
        suffix_words = " ".join([self._random_word() for _ in range(random.randint(2, 5))])

        text = f"{prefix_words} ${ticker_1} {mid_words} {ticker_2} {suffix_words} ${ticker_3}"
        extracted = extract_tickers(text)

        self.assertIsInstance(extracted, (list, set, tuple))
        extracted_set = set(extracted)
        self.assertIn(ticker_1, extracted_set)
        self.assertIn(ticker_2, extracted_set)
        self.assertIn(ticker_3, extracted_set)

    def test_extract_tickers_no_false_positives(self):
        plain_text = " ".join([self._random_word() for _ in range(random.randint(15, 30))])
        extracted = extract_tickers(plain_text)
        self.assertEqual(len(extracted), 0)

    def test_fetch_html_success(self):
        target_url = self._random_url()
        random_token = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        mock_html_body = f"<html><body><div