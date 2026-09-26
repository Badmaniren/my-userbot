import os
import sys
import unittest
import uuid
import random
from datetime import datetime

from skills.market_news_fetcher import MarketNewsFetcher
import skills.market_parser as market_parser
import skills.db_storage as db_storage


class TestMarketNewsFetcherIntegration(unittest.TestCase):
    def setUp(self):
        self.fetcher = MarketNewsFetcher()
        self.random_tag = uuid.uuid4().hex[:8]
        self.ticker_1 = f"TCK{random.randint(100, 999)}"
        self.ticker_2 = f"FIN{random.randint(100, 999)}"
        self.ticker_crypto = f"CRY{random.randint(100, 999)}"
        self.source_id = f"source_{self.random_tag}"

    def tearDown(self):
        pass

    def test_extract_financial_tickers_from_unstructured_text(self):
        headline_uuid = uuid.uuid4().hex
        sample_text = (
            f"Breaking News [{headline_uuid}]: Bullish breakout on ${self.ticker_1} "
            f"following strong Q3 guidance, while NASDAQ:{self.ticker_2} and {self.ticker_crypto} "
            f"show sudden momentum shifts across market desks."
        )

        extracted_tickers = self.fetcher.extract_tickers(sample_text)

        self.assertIsInstance(extracted_tickers, list)
        normalized_tickers = [t.upper().replace("$", "").split(":")[-1] for t in extracted_tickers]
        self.assertIn(self.ticker_1, normalized_tickers)
        self.assertIn(self.ticker_2, normalized_tickers)
        self.assertIn(self.ticker_crypto, normalized_tickers)

    def test_fetch_and_parse_news_headlines_integration(self):
        item_id_1 = f"news_{uuid.uuid4().hex}"
        item_id_2 = f"news_{uuid.uuid4().hex}"
        title_1 = f"Surge in {self.ticker_1} options volume after dividend hike ({item_id_1})"
        title_2 = f"Analyst downgrades {self.ticker_2} amid supply constraints ({item_id_2})"

        raw_feed_content = f"""
        <html>
            <body>
                <article class="news-item" id="{item_id_1}">
                    <h2>{title_1}</h2>
                    <p>Shares of ${self.ticker_1} rallied by 5% today.</p>
                </article>
                <article class="news-item" id="{item_id_2}">
                    <h2>{title_2}</h2>
                    <p>Cautious outlook on NASDAQ:{self.ticker_2} affects price targets.</p>
                </article>
            </body>
        </html>
        """

        parsed_items = self.fetcher.fetch_news(raw_feed_content, source=self.source_id)

        self.assertIsInstance(parsed_items, list)
        self.assertGreaterEqual(len(parsed_items), 2)

        titles = [item.get("title", "") for item in parsed_items]
        self.assertTrue(any(title_1 in t for t in titles))
        self.assertTrue(any(title_2 in t for t in titles))

        matched_item_1 = next(item for item in parsed_items if title_1 in item.get("title", ""))
        item_1_tickers = [t.upper().replace("$", "") for t in matched_item_1.get("tickers", [])]
        self.assertIn(self.ticker_1, item_1_tickers)
        self.assertEqual(matched_item_1.get("source"), self.source_id)

    def test_pipeline_persistence_integration_with_db_storage(self):
        unique_news_id = f"persist_{uuid.uuid4().hex}"
        headline = f"Strategic acquisition announced by {self.ticker_1} targeting {self.ticker_2}"
        raw_article = f"<item><title>{headline}</title><guid>{unique_news_id}</guid></item>"

        fetched_articles = self.fetcher.fetch_news(raw_article, source=self.source_id)
        self.assertTrue(any(unique_news_id in str(item) or headline in item.get("title", "") for item in fetched_articles))

        saved_count = self.fetcher.save_to_storage(fetched_articles)
        self.assertIsInstance(saved_count, int)
        self.assertGreater(saved_count, 0)

        if hasattr(self.fetcher, "get_stored_news"):
            stored_records = self.fetcher.get_stored_news(source=self.source_id)
            self.assertTrue(any(headline in r.get("title", "") for r in stored_records))


if __name__ == "__main__":
    unittest.main()