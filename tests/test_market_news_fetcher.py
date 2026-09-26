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

    def test_extract_tickers_empty_or_none(self):
        self.assertEqual(extract_tickers(""), [])
        self.assertEqual(extract_tickers(None), [])

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

    def test_extract_tickers_stop_words_filtered(self):
        text = "THE AND FOR BUT Q1 Q2 Q3 Q4"
        extracted = extract_tickers(text)
        for word in ["THE", "AND", "FOR", "BUT", "Q1", "Q2", "Q3", "Q4"]:
            self.assertNotIn(word, extracted)

    def test_fetch_html_success(self):
        target_url = self._random_url()
        random_token = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        mock_html_body = f"<html><body><div id='content'>{random_token}</div></body></html>"

        mock_response = MagicMock()
        mock_response.text = mock_html_body
        mock_response.raise_for_status.return_value = None

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = self.fetcher.fetch_html(target_url)
            mock_get.assert_called_once_with(target_url, timeout=10)
            mock_response.raise_for_status.assert_called_once()
            self.assertEqual(result, mock_html_body)

    def test_fetch_html_error(self):
        target_url = self._random_url()
        with patch("requests.get", side_effect=requests.RequestException("Connection error")):
            with self.assertRaises(requests.RequestException):
                self.fetcher.fetch_html(target_url)

    def test_fetch_news_url_input(self):
        target_url = self._random_url()
        ticker = self._random_ticker()
        mock_content = f"<html><body><article><h1>Headline for ${ticker}</h1><p>Body text</p></article></body></html>"

        with patch.object(self.fetcher, "fetch_html", return_value=mock_content) as mock_fetch:
            items = self.fetcher.fetch_news(target_url, source="web")
            mock_fetch.assert_called_once_with(target_url)
            self.assertEqual(len(items), 1)
            self.assertIn(ticker, items[0]["tickers"])
            self.assertEqual(items[0]["source"], "web")

    def test_fetch_news_empty_content(self):
        items = self.fetcher.fetch_news("", source="test")
        self.assertEqual(items, [])

    def test_fetch_news_fallback_no_articles(self):
        ticker = self._random_ticker()
        content = f"<html><head><title>Market Update ${ticker}</title></head><body>Plain page content</body></html>"
        items = self.fetcher.fetch_news(content, source="fallback_src")
        self.assertEqual(len(items), 1)
        self.assertIn("Market Update", items[0]["title"])
        self.assertIn(ticker, items[0]["tickers"])
        self.assertEqual(items[0]["source"], "fallback_src")

    def test_fetch_news_with_articles_and_items(self):
        ticker1 = self._random_ticker()
        ticker2 = self._random_ticker()
        xml_content = f"""
        <rss>
            <channel>
                <item id="item1">
                    <title>Report on ${ticker1}</title>
                    <description>Details regarding {ticker1} earnings.</description>
                </item>
                <article id="art1">
                    <h2>Analysis of ${ticker2}</h2>
                    <content>Growth projected for {ticker2}.</content>
                </article>
            </channel>
        </rss>
        """
        items = self.fetcher.fetch_news(xml_content, source="rss")
        self.assertEqual(len(items), 2)
        self.assertIn(ticker1, items[0]["tickers"])
        self.assertEqual(items[0]["id"], "item1")
        self.assertIn(ticker2, items[1]["tickers"])

    def test_storage_and_retrieval(self):
        ticker = self._random_ticker()
        items = [
            {"title": f"News 1 {ticker}", "source": "src_a", "tickers": [ticker]},
            {"title": f"News 2 {ticker}", "source": "src_b", "tickers": [ticker]}
        ]
        saved_count = self.fetcher.save_to_storage(items)
        self.assertEqual(saved_count, 2)

        all_stored = self.fetcher.get_stored_news()
        self.assertEqual(len(all_stored), 2)

        src_a_stored = self.fetcher.get_stored_news(source="src_a")
        self.assertEqual(len(src_a_stored), 1)
        self.assertEqual(src_a_stored[0]["title"], f"News 1 {ticker}")


if __name__ == "__main__":
    unittest.main()
