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
        domain = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
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

    @patch("requests.get")
    def test_fetch_html_success(self, mock_get):
        target_url = self._random_url()
        random_token = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        mock_html_body = f"<html><body><div>{random_token}</div></body></html>"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_html_body
        mock_get.return_value = mock_response

        res = self.fetcher.fetch_html(target_url)
        self.assertEqual(res, mock_html_body)
        mock_get.assert_called_once_with(target_url, timeout=10)

    def test_fetch_news_articles_html(self):
        html_content = """
        <html>
            <body>
                <article id="art1">
                    <h2>Stock Market $AAPL Update</h2>
                    <p>Apple Inc stock risen today NASDAQ:AAPL</p>
                </article>
                <article id="art2">
                    <h2>Crypto Surge $BTC</h2>
                    <p>Bitcoin trading high</p>
                </article>
            </body>
        </html>
        """
        items = self.fetcher.fetch_news(html_content, source="test_source")
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["id"], "art1")
        self.assertIn("AAPL", items[0]["tickers"])
        self.assertEqual(items[0]["source"], "test_source")
        self.assertEqual(items[1]["id"], "art2")
        self.assertIn("BTC", items[1]["tickers"])

    def test_fetch_news_no_articles(self):
        html_content = "<html><body><h1>Market Summary $MSFT</h1><p>General news text</p></body></html>"
        items = self.fetcher.fetch_news(html_content)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["title"], "Market Summary $MSFT")
        self.assertIn("MSFT", items[0]["tickers"])

    @patch("skills.market_news_fetcher.MarketNewsFetcher.fetch_html")
    def test_fetch_news_from_url(self, mock_fetch_html):
        url = "https://example.com/news"
        mock_fetch_html.return_value = "<html><body><h1>Headline $GOOG</h1></body></html>"

        items = self.fetcher.fetch_news(url, source="web_source")
        mock_fetch_html.assert_called_once_with(url)
        self.assertEqual(len(items), 1)
        self.assertIn("GOOG", items[0]["tickers"])
        self.assertEqual(items[0]["source"], "web_source")

    def test_save_and_get_stored_news(self):
        items = [
            {"title": "News 1", "source": "srcA"},
            {"title": "News 2", "source": "srcB"}
        ]
        count = self.fetcher.save_to_storage(items)
        self.assertEqual(count, 2)

        stored_all = self.fetcher.get_stored_news()
        self.assertEqual(len(stored_all), 2)

        stored_srcA = self.fetcher.get_stored_news(source="srcA")
        self.assertEqual(len(stored_srcA), 1)
        self.assertEqual(stored_srcA[0]["title"], "News 1")
